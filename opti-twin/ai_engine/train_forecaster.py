"""Train the M2 tariff/load forecaster (planing-v2.md §6).

Reads featurised Parquet (with sim_hour_sin/cos already computed by
`data_pipeline/featurize.py`) and trains an LSTM with two heads:
  - price quantiles (5 quantiles + mean) over the next 600 sim-ticks
  - mean expected arc-power load over the next 600 sim-ticks

Loss = pinball(price quantiles) + 0.1 * MSE(price mean) + 0.5 * MSE(load).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Tuple

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

# torch BEFORE pandas (pyarrow-MKL conflict on Windows).
import numpy as np
import torch
import torch.nn as nn
import pandas as pd  # noqa: E402

from forecaster.lstm_forecaster import (
    FORECAST_HORIZON,
    LOOKBACK,
    N_INPUT_FEATURES,
    N_PRICE_OUTPUTS,
    QUANTILES,
    TariffLoadForecaster,
    pinball_loss,
)

DEFAULT_DATA_ROOT = HERE.parent / "data"

INPUT_COLUMNS = [
    "electricity_price",
    "arc_power_mw",
    "is_peak",
    "tou_mode",
    "sim_hour_sin",
    "sim_hour_cos",
    "grid_frequency",
]
PRICE_TARGET = "electricity_price"
LOAD_TARGET = "arc_power_mw"


def _build_windows(
    df: pd.DataFrame, lookback: int, horizon: int
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return (X[N, L, F], price_y[N, H], load_y[N, H]).

    Slides a (lookback + horizon) window across each episode independently.
    """
    df = df.sort_values(["episode_id", "step_id"]).reset_index(drop=True)

    X: list[np.ndarray] = []
    Yp: list[np.ndarray] = []
    Yl: list[np.ndarray] = []

    for _, sub in df.groupby("episode_id"):
        full = sub[INPUT_COLUMNS + [PRICE_TARGET, LOAD_TARGET]].to_numpy(dtype=np.float32)
        if len(full) < lookback + horizon:
            continue
        in_arr = full[:, : len(INPUT_COLUMNS)]
        price_arr = full[:, len(INPUT_COLUMNS)]      # PRICE_TARGET
        load_arr = full[:, len(INPUT_COLUMNS) + 1]   # LOAD_TARGET
        for start in range(len(full) - lookback - horizon + 1):
            X.append(in_arr[start : start + lookback])
            Yp.append(price_arr[start + lookback : start + lookback + horizon])
            Yl.append(load_arr[start + lookback : start + lookback + horizon])

    if not X:
        return (
            np.empty((0, lookback, N_INPUT_FEATURES), dtype=np.float32),
            np.empty((0, horizon), dtype=np.float32),
            np.empty((0, horizon), dtype=np.float32),
        )
    return np.stack(X, 0), np.stack(Yp, 0), np.stack(Yl, 0)


def _normalise(X: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    means = X.mean(axis=(0, 1)).astype(np.float32)
    stds = X.std(axis=(0, 1)).astype(np.float32) + 1e-6
    return (X - means[None, None, :]) / stds[None, None, :], means, stds


def _coverage(y: np.ndarray, q_lo: np.ndarray, q_hi: np.ndarray) -> float:
    return float(np.mean((y >= q_lo) & (y <= q_hi)))


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--train", default=str(DEFAULT_DATA_ROOT / "processed" / "train" / "data.parquet"))
    p.add_argument("--val", default=str(DEFAULT_DATA_ROOT / "processed" / "val" / "data.parquet"))
    p.add_argument("--out", default=str(HERE / "models" / "forecaster" / "v0.1.0"))
    p.add_argument("--lookback", type=int, default=LOOKBACK)
    p.add_argument("--horizon", type=int, default=FORECAST_HORIZON)
    p.add_argument("--max-windows", type=int, default=20000,
                   help="cap on training windows to keep one epoch reasonable on CPU")
    p.add_argument("--epochs", type=int, default=20)
    p.add_argument("--batch", type=int, default=128)
    p.add_argument("--lr", type=float, default=1e-3)
    p.add_argument("--seed", type=int, default=42)
    args = p.parse_args()

    torch.manual_seed(args.seed)
    np.random.seed(args.seed)

    train_df = pd.read_parquet(args.train)
    val_df = pd.read_parquet(args.val)
    print(f"[forecaster] train rows={len(train_df)}  val rows={len(val_df)}")

    Xt, Pt, Lt = _build_windows(train_df, args.lookback, args.horizon)
    Xv, Pv, Lv = _build_windows(val_df, args.lookback, args.horizon)
    print(f"[forecaster] windows  train={len(Xt)}  val={len(Xv)}")
    if len(Xt) == 0:
        raise SystemExit("[forecaster] no training windows -- collect more episodes")

    if len(Xt) > args.max_windows:
        rng = np.random.default_rng(args.seed)
        idx = rng.choice(len(Xt), size=args.max_windows, replace=False)
        Xt, Pt, Lt = Xt[idx], Pt[idx], Lt[idx]
        print(f"[forecaster] sub-sampled to {len(Xt)} train windows")

    Xt_norm, means, stds = _normalise(Xt)
    Xv_norm = (Xv - means[None, None, :]) / stds[None, None, :]

    Xt_t = torch.from_numpy(Xt_norm).float()
    Pt_t = torch.from_numpy(Pt).float()
    Lt_t = torch.from_numpy(Lt).float()
    Xv_t = torch.from_numpy(Xv_norm).float()
    Pv_t = torch.from_numpy(Pv).float()
    Lv_t = torch.from_numpy(Lv).float()

    model = TariffLoadForecaster(
        input_dim=N_INPUT_FEATURES,
        hidden=128,
        horizon=args.horizon,
        n_price_outputs=N_PRICE_OUTPUTS,
    )
    optim = torch.optim.Adam(model.parameters(), lr=args.lr)

    best_val = float("inf")
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    for ep in range(args.epochs):
        model.train()
        perm = torch.randperm(len(Xt_t))
        ep_loss = 0.0
        for i in range(0, len(perm), args.batch):
            idx = perm[i : i + args.batch]
            x = Xt_t[idx]
            y_price = Pt_t[idx]
            y_load = Lt_t[idx]
            price_pred, load_pred = model(x)  # price_pred: (B, H, n_outputs)

            loss_q = pinball_loss(y_price, price_pred, QUANTILES)
            loss_mean = nn.functional.mse_loss(price_pred[..., 0], y_price)
            loss_load = nn.functional.mse_loss(load_pred, y_load)
            loss = loss_q + 0.1 * loss_mean + 0.5 * loss_load
            optim.zero_grad()
            loss.backward()
            optim.step()
            ep_loss += float(loss) * len(idx)
        ep_loss /= len(Xt_t)

        # Validation
        model.eval()
        with torch.no_grad():
            price_v, load_v = model(Xv_t)
            val_q = float(pinball_loss(Pv_t, price_v, QUANTILES))
            val_mean = float(nn.functional.mse_loss(price_v[..., 0], Pv_t))
            val_load = float(nn.functional.mse_loss(load_v, Lv_t))
            # 90% PI coverage
            q_lo = price_v[..., 1].cpu().numpy()  # p05
            q_hi = price_v[..., 5].cpu().numpy()  # p95
            cov = _coverage(Pv_t.cpu().numpy(), q_lo, q_hi)
        val_total = val_q + 0.1 * val_mean + 0.5 * val_load
        print(
            f"[forecaster] epoch {ep+1:2d}/{args.epochs}  train={ep_loss:.4f}  "
            f"val_q={val_q:.4f}  val_load_mse={val_load:.4f}  90pi_coverage={cov:.3f}"
        )
        if val_total < best_val:
            best_val = val_total
            torch.save(model.state_dict(), out_dir / "forecaster.pt")
            with open(out_dir / "feature_columns.json", "w") as f:
                json.dump({
                    "feature_columns": INPUT_COLUMNS,
                    "feature_means": means.tolist(),
                    "feature_stds": stds.tolist(),
                    "input_dim": N_INPUT_FEATURES,
                    "hidden": 128,
                    "horizon": args.horizon,
                    "n_price_outputs": N_PRICE_OUTPUTS,
                    "quantiles": list(QUANTILES),
                    "price_target": PRICE_TARGET,
                    "load_target": LOAD_TARGET,
                }, f, indent=2)

    print(f"[forecaster] best val_total={best_val:.4f}  saved to {out_dir}")


if __name__ == "__main__":
    main()
