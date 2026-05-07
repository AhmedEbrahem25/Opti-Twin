"""Train the M3 anomaly autoencoder (planing-v2.md §7.3).

Trains *only* on no-crisis transitions, so the model learns the "normal"
manifold. Calibrates the threshold to the 95th-percentile reconstruction
error on the held-out training distribution. Saves to
`models/anomaly/v0.1.0/{autoencoder.pt, threshold.json}`.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

# Import torch BEFORE pandas/pyarrow — on Windows, pyarrow loads its own MKL
# build whose symbol resolution conflicts with torch's, producing a hard
# segfault (STATUS_ACCESS_VIOLATION) the moment the optimiser allocates state.
import numpy as np
import torch
import torch.nn as nn
import pandas as pd  # noqa: E402  — must follow torch

from anomaly.autoencoder import N_CHANNELS, WINDOW_LEN, TelemetryAutoencoder
from data_pipeline.schema import ANOMALY_CHANNELS

DEFAULT_DATA_ROOT = HERE.parent / "data"


def _crisis_mask(df: pd.DataFrame) -> pd.Series:
    """True where any crisis flag is set on this row."""
    return (
        df["crisis_wall_overheat"].astype(bool)
        | df["crisis_grid_spike"].astype(bool)
        | df["crisis_transformer_alarm"].astype(bool)
    )


def _build_windows(df: pd.DataFrame, channels: list[str], window: int) -> np.ndarray:
    """Slide a `window`-tick frame over each episode; return (N, C, T) array.

    Crisis windows are excluded — any row inside the window with a crisis flag
    causes that window to be dropped.
    """
    df = df.sort_values(["episode_id", "step_id"]).reset_index(drop=True)
    crisis = _crisis_mask(df).to_numpy()

    out: list[np.ndarray] = []
    for ep_id, sub in df.groupby("episode_id"):
        idx = sub.index.to_numpy()
        if len(idx) < window:
            continue
        chan = sub[channels].to_numpy(dtype=np.float32).T  # (C, T_ep)
        for start in range(0, len(idx) - window + 1):
            ep_slice = idx[start : start + window]
            if crisis[ep_slice].any():
                continue
            out.append(chan[:, start : start + window])
    if not out:
        return np.empty((0, len(channels), window), dtype=np.float32)
    return np.stack(out, axis=0)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--train", default=str(DEFAULT_DATA_ROOT / "processed" / "train" / "data.parquet"))
    p.add_argument("--val", default=str(DEFAULT_DATA_ROOT / "processed" / "val" / "data.parquet"))
    p.add_argument("--out", default=str(HERE / "models" / "anomaly" / "v0.1.0"))
    p.add_argument("--epochs", type=int, default=30)
    p.add_argument("--batch", type=int, default=64)
    p.add_argument("--lr", type=float, default=1e-3)
    p.add_argument("--threshold-pct", type=float, default=95.0,
                   help="Percentile of train recon error to use as threshold")
    p.add_argument("--seed", type=int, default=42)
    args = p.parse_args()

    torch.manual_seed(args.seed)
    np.random.seed(args.seed)

    train_df = pd.read_parquet(args.train)
    val_df = pd.read_parquet(args.val)
    print(f"[anomaly] train rows={len(train_df)}  val rows={len(val_df)}")

    train_windows = _build_windows(train_df, ANOMALY_CHANNELS, WINDOW_LEN)
    val_windows = _build_windows(val_df, ANOMALY_CHANNELS, WINDOW_LEN)
    print(f"[anomaly] no-crisis windows  train={len(train_windows)}  val={len(val_windows)}")
    if len(train_windows) == 0:
        raise SystemExit("[anomaly] no clean windows in training data -- collect more episodes")

    # Per-channel z-score using train stats so reconstruction loss is balanced.
    channel_means = train_windows.mean(axis=(0, 2)).astype(np.float32)
    channel_stds = train_windows.std(axis=(0, 2)).astype(np.float32) + 1e-6
    train_norm = (train_windows - channel_means[None, :, None]) / channel_stds[None, :, None]
    val_norm = (val_windows - channel_means[None, :, None]) / channel_stds[None, :, None]

    model = TelemetryAutoencoder(channels=N_CHANNELS, window=WINDOW_LEN)
    optim = torch.optim.Adam(model.parameters(), lr=args.lr)
    loss_fn = nn.MSELoss()

    train_t = torch.from_numpy(train_norm).float()
    val_t = torch.from_numpy(val_norm).float() if len(val_norm) else None

    best_val = float("inf")
    for ep in range(args.epochs):
        model.train()
        perm = torch.randperm(len(train_t))
        ep_loss = 0.0
        for i in range(0, len(perm), args.batch):
            idx = perm[i : i + args.batch]
            x = train_t[idx]
            recon = model(x)
            loss = loss_fn(recon, x)
            optim.zero_grad()
            loss.backward()
            optim.step()
            ep_loss += float(loss) * len(idx)
        ep_loss /= len(train_t)
        val_loss = float("nan")
        if val_t is not None and len(val_t) > 0:
            model.eval()
            with torch.no_grad():
                val_loss = float(loss_fn(model(val_t), val_t))
        print(f"[anomaly] epoch {ep+1:2d}/{args.epochs}  train_loss={ep_loss:.5f}  val_loss={val_loss:.5f}")
        if val_loss < best_val:
            best_val = val_loss

    # Calibrate threshold on training set
    model.eval()
    with torch.no_grad():
        train_err = model.reconstruction_error(train_t).cpu().numpy()
    threshold = float(np.percentile(train_err, args.threshold_pct))
    print(f"[anomaly] threshold ({args.threshold_pct}th pctile) = {threshold:.5f}")

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    torch.save(model.state_dict(), out_dir / "autoencoder.pt")
    with open(out_dir / "threshold.json", "w") as f:
        json.dump({
            "threshold": threshold,
            "threshold_pct": args.threshold_pct,
            "channel_means": channel_means.tolist(),
            "channel_stds": channel_stds.tolist(),
            "channels": ANOMALY_CHANNELS,
            "window": WINDOW_LEN,
            "train_recon_p50": float(np.percentile(train_err, 50)),
            "train_recon_p99": float(np.percentile(train_err, 99)),
        }, f, indent=2)
    print(f"[anomaly] saved model -> {out_dir}")


if __name__ == "__main__":
    main()
