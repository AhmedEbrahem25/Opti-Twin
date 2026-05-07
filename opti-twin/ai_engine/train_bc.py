"""Standalone M4 trainer (planing-v2.md §8).

Loads the scripted-teacher Parquet rollouts produced by `collect_episodes.py`,
trains a BCNet to imitate the action_id column, and saves the weights so that
`train_ppo.py --bc-init <path>` can pick them up.

Reads obs from the env's `make_obs_vector` so any future obs-space change in
`environment.py` is automatically reflected here.

If `--forecaster` and `--anomaly` paths are passed, the BC obs vector includes
M2/M3 outputs computed by replaying each episode's rolling lookback window.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Tuple

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

# Import torch BEFORE pandas — on Windows, pyarrow's MKL build conflicts with
# torch's symbols if loaded first. See train_anomaly.py for the failure mode.
import numpy as np
import torch
import torch.nn as nn
import pandas as pd  # noqa: E402

from environment import ACTIONS, OBS_DIM, make_obs_vector
from policies.bc_policy import BCNet

DEFAULT_DATA_ROOT = HERE.parent / "data"


def _row_to_state(row: pd.Series) -> dict:
    """Reconstruct the env state dict that produced this transition."""
    return {
        "electricity_price": float(row["electricity_price"]),
        "is_peak": bool(row["is_peak"]),
        "grid_frequency": float(row["grid_frequency"]),
        "furnace_bath_temp": float(row["furnace_bath_temp"]),
        "electrode_temp": float(row["electrode_temp"]),
        "wall_panel_temp": float(row["wall_panel_temp"]),
        "cooling_water_outlet_temp": float(row["cooling_water_outlet_temp"]),
        "heat_progress_pct": float(row["heat_progress_pct"]),
        "current_batch_weight": float(row["current_batch_weight"]),
        "batches_today": int(row["batches_today"]),
        "production_backlog": int(row["production_backlog"]),
        "arc_power_mw": float(row["arc_power_mw"]),
        "power_factor": float(row["power_factor"]),
        "energy_this_heat_kwh": float(row["energy_this_heat_kwh"]),
        "electrode_position_mm": float(row["electrode_position_mm"]),
        "electrode_consumption_kg": float(row["electrode_consumption_kg"]),
        "tou_mode": bool(row["tou_mode"]),
        "sim_hour": float(row["sim_hour"]),
    }


def _state_to_forecast_features(s: dict) -> np.ndarray:
    sh = float(s.get("sim_hour", 0.0))
    rad = 2.0 * np.pi * sh / 24.0
    return np.array([
        float(s.get("electricity_price", 1.60)),
        float(s.get("arc_power_mw", 0.0)),
        1.0 if s.get("is_peak", False) else 0.0,
        1.0 if s.get("tou_mode", False) else 0.0,
        float(np.sin(rad)),
        float(np.cos(rad)),
        float(s.get("grid_frequency", 50.0)),
    ], dtype=np.float32)


def _state_to_anomaly_channels(s: dict) -> np.ndarray:
    return np.array([
        float(s.get("arc_power_mw", 0.0)),
        float(s.get("furnace_bath_temp", 0.0)),
        float(s.get("wall_panel_temp", 0.0)),
        float(s.get("electrode_temp", 0.0)),
        float(s.get("cooling_water_outlet_temp", 0.0)),
        float(s.get("power_factor", 0.0)),
        float(s.get("energy_this_heat_kwh", 0.0)),
        float(s.get("electrode_consumption_kg", 0.0)),
        float(s.get("grid_frequency", 50.0)),
    ], dtype=np.float32)


def parquet_to_arrays(
    parquet_path: Path,
    *,
    forecaster=None,
    anomaly_detector=None,
    forecast_refresh_every: int = 10,
) -> Tuple[np.ndarray, np.ndarray]:
    df = pd.read_parquet(parquet_path)
    df = df.sort_values(["episode_id", "step_id"]).reset_index(drop=True)
    actions = df["action_id"].to_numpy(dtype=np.int64)

    if forecaster is None and anomaly_detector is None:
        # Fast path: vectorisable build with zero M2/M3.
        obs = np.stack([make_obs_vector(_row_to_state(r)) for _, r in df.iterrows()], axis=0)
        return obs.astype(np.float32), actions

    # Slow path: replay each episode through M2/M3 rolling windows.
    from forecaster import LOOKBACK as F_LB, summarise_for_obs
    obs_list: list[np.ndarray] = []
    for _, sub in df.groupby("episode_id"):
        f_window = np.zeros((F_LB, 7), dtype=np.float32) if forecaster is not None else None
        a_window = (np.zeros((anomaly_detector.model.channels, anomaly_detector.model.window),
                              dtype=np.float32)
                    if anomaly_detector is not None else None)
        cached_summary = None
        cached_anomaly = 0.0
        sub = sub.reset_index(drop=True)
        for step_idx, (_, row) in enumerate(sub.iterrows()):
            state = _row_to_state(row)
            if f_window is not None:
                f_window = np.roll(f_window, -1, axis=0)
                f_window[-1] = _state_to_forecast_features(state)
                if step_idx % forecast_refresh_every == 0:
                    price_q, _ = forecaster.predict(f_window)
                    cached_summary = summarise_for_obs(price_q)
            if a_window is not None:
                a_window = np.roll(a_window, -1, axis=1)
                a_window[:, -1] = _state_to_anomaly_channels(state)
                ch_means = anomaly_detector.channel_means[:, None]
                ch_stds = anomaly_detector.channel_stds[:, None] + 1e-6
                normed = (a_window - ch_means) / ch_stds
                cached_anomaly = anomaly_detector.score(normed.astype(np.float32))
            obs_list.append(make_obs_vector(
                state,
                forecast_summary=cached_summary,
                anomaly_score=cached_anomaly,
            ))
    obs = np.stack(obs_list, axis=0)
    return obs.astype(np.float32), actions


def train(net: BCNet, obs_t: torch.Tensor, act_t: torch.Tensor, *,
          val_obs: torch.Tensor, val_act: torch.Tensor,
          epochs: int, batch_size: int, lr: float) -> None:
    optim = torch.optim.Adam(net.parameters(), lr=lr)
    loss_fn = nn.CrossEntropyLoss()
    n = len(obs_t)
    print(f"[BC] training on {n} pairs, {epochs} epochs, batch={batch_size}")
    for ep in range(epochs):
        net.train()
        perm = torch.randperm(n)
        ep_loss = 0.0
        ep_correct = 0
        for i in range(0, n, batch_size):
            idx = perm[i : i + batch_size]
            logits = net(obs_t[idx])
            loss = loss_fn(logits, act_t[idx])
            optim.zero_grad()
            loss.backward()
            optim.step()
            ep_loss += float(loss) * len(idx)
            ep_correct += int((logits.argmax(-1) == act_t[idx]).sum())
        net.eval()
        with torch.no_grad():
            val_logits = net(val_obs)
            val_acc = float((val_logits.argmax(-1) == val_act).float().mean())
        print(
            f"[BC] epoch {ep+1:2d}/{epochs}  loss={ep_loss/n:.4f}  "
            f"train_acc={ep_correct/n:.3f}  val_acc={val_acc:.3f}"
        )


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--train", default=str(DEFAULT_DATA_ROOT / "processed" / "train" / "data.parquet"))
    p.add_argument("--val", default=str(DEFAULT_DATA_ROOT / "processed" / "val" / "data.parquet"))
    p.add_argument("--out", default=str(HERE / "models" / "bc" / "v0.1.0" / "bc_init.pt"))
    p.add_argument("--forecaster", default=None,
                   help="Path to M2 forecaster directory; populates obs dims 16-21")
    p.add_argument("--anomaly", default=None,
                   help="Path to M3 anomaly detector directory; populates obs dim 38")
    p.add_argument("--epochs", type=int, default=10)
    p.add_argument("--batch", type=int, default=256)
    p.add_argument("--lr", type=float, default=3e-4)
    p.add_argument("--seed", type=int, default=42)
    args = p.parse_args()

    torch.manual_seed(args.seed)
    np.random.seed(args.seed)

    forecaster = None
    anomaly_detector = None
    if args.forecaster:
        from forecaster.lstm_forecaster import load_forecaster
        forecaster = load_forecaster(args.forecaster)
        print(f"[BC] M2 forecaster loaded from {args.forecaster}")
    if args.anomaly:
        from anomaly.autoencoder import load_anomaly_detector
        anomaly_detector = load_anomaly_detector(args.anomaly)
        print(f"[BC] M3 anomaly detector loaded from {args.anomaly}")

    print(f"[BC] loading train Parquet from {args.train}")
    train_obs, train_act = parquet_to_arrays(
        Path(args.train), forecaster=forecaster, anomaly_detector=anomaly_detector,
    )
    print(f"[BC] loading val Parquet from {args.val}")
    val_obs, val_act = parquet_to_arrays(
        Path(args.val), forecaster=forecaster, anomaly_detector=anomaly_detector,
    )

    print(f"[BC] OBS_DIM={OBS_DIM}  n_actions={len(ACTIONS)}")
    print(f"[BC] action distribution (train):")
    counts = np.bincount(train_act, minlength=len(ACTIONS))
    for i, lab in enumerate(ACTIONS):
        n = int(counts[i])
        print(f"     {lab:<22} {n:6d}  ({n/len(train_act)*100:.1f}%)")

    net = BCNet(obs_dim=OBS_DIM, n_actions=len(ACTIONS))
    train(
        net,
        torch.from_numpy(train_obs),
        torch.from_numpy(train_act),
        val_obs=torch.from_numpy(val_obs),
        val_act=torch.from_numpy(val_act),
        epochs=args.epochs,
        batch_size=args.batch,
        lr=args.lr,
    )

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(net.state_dict(), out_path)
    print(f"[BC] saved -> {out_path}")


if __name__ == "__main__":
    main()
