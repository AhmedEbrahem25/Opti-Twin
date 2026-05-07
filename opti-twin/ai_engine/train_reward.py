"""Train the M5 preference reward model (planing-v2.md §9).

The hackathon doesn't have a real human-rater labelled dataset, so we
synthesise preferences from a deterministic oracle (planing-v2.md §9.3):
  - count safety violations per trajectory (wall_panel_temp > 240, PF
    penalty active, grid_freq < 49.7 untreated)
  - count quality bonuses (bath in [1600, 1650])
  - count missed-heat backlog
  - oracle prefers the trajectory with the lower violation+backlog count
    and higher quality bonus

200 trajectory pairs are sampled from `data/processed/train/`. Each
trajectory is a 50-frame slice of a single episode.

Outputs:
  - `models/reward_model/v0.1.0/reward_model.pt`
  - `models/reward_model/v0.1.0/meta.json` (state_dim, normalisation stats)
  - `data/preferences/oracle_v1.jsonl` (audit trail of pairs + labels)
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import List, Tuple

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

# torch BEFORE pandas (pyarrow MKL conflict on Windows).
import numpy as np
import torch
import torch.nn as nn
import pandas as pd  # noqa: E402

from environment import ACTIONS
from reward_model import N_ACTIONS, REWARD_STATE_DIM, PrefRewardModel

DEFAULT_DATA_ROOT = HERE.parent / "data"
TRAJ_LEN = 50


def _state_projection(row: pd.Series, forecast_summary: np.ndarray, anomaly_score: float) -> np.ndarray:
    """Build the 23-D semantic state projection used by M5.

    Layout (matches the BC obs prefix):
       [0..15]:   telemetry block from environment.make_obs_vector dims 0-15
                  but read directly from row columns to avoid running the
                  full obs builder per-row.
       [16..21]:  M2 6-D forecast summary
       [22]:      M3 anomaly score
    """
    telemetry = np.array([
        (float(row["electricity_price"]) - 1.0) / 1.5,
        1.0 if bool(row["is_peak"]) else 0.0,
        (float(row["grid_frequency"]) - 49.5) / 1.0,
        (float(row["furnace_bath_temp"]) - 1200.0) / 480.0,
        (float(row["electrode_temp"]) - 1500.0) / 1500.0,
        (float(row["wall_panel_temp"]) - 80.0) / 170.0,
        (float(row["cooling_water_outlet_temp"]) - 25.0) / 30.0,
        float(row["heat_progress_pct"]) / 100.0,
        (float(row["current_batch_weight"]) - 80.0) / 105.0,
        float(row["batches_today"]) / 24.0,
        float(row["production_backlog"]) / 5.0,
        float(row["arc_power_mw"]) / 200.0,
        (float(row["power_factor"]) - 0.6) / 0.35,
        float(row["energy_this_heat_kwh"]) / 100000.0,
        float(row["electrode_position_mm"]) / 500.0,
        float(row["electrode_consumption_kg"]) / 0.2,
    ], dtype=np.float32)
    return np.concatenate([telemetry, forecast_summary, [anomaly_score]])


def _replay_episode(
    sub: pd.DataFrame,
    forecaster,
    anomaly_detector,
) -> List[np.ndarray]:
    """Walk one episode, building the 23-D semantic state per row."""
    from forecaster import LOOKBACK as F_LB, summarise_for_obs

    f_window = np.zeros((F_LB, 7), dtype=np.float32) if forecaster is not None else None
    a_window = (np.zeros((anomaly_detector.model.channels, anomaly_detector.model.window),
                         dtype=np.float32)
                if anomaly_detector is not None else None)
    cached_summary = np.zeros(6, dtype=np.float32)
    cached_anomaly = 0.0

    states: List[np.ndarray] = []
    sub = sub.sort_values("step_id").reset_index(drop=True)
    for step_idx, (_, row) in enumerate(sub.iterrows()):
        if f_window is not None:
            sh = float(row["sim_hour"])
            rad = 2.0 * np.pi * sh / 24.0
            feat_row = np.array([
                float(row["electricity_price"]),
                float(row["arc_power_mw"]),
                1.0 if bool(row["is_peak"]) else 0.0,
                1.0 if bool(row["tou_mode"]) else 0.0,
                float(np.sin(rad)),
                float(np.cos(rad)),
                float(row["grid_frequency"]),
            ], dtype=np.float32)
            f_window = np.roll(f_window, -1, axis=0)
            f_window[-1] = feat_row
            if step_idx % 10 == 0:
                price_q, _ = forecaster.predict(f_window)
                cached_summary = summarise_for_obs(price_q)
        if a_window is not None:
            ch_row = np.array([
                float(row["arc_power_mw"]), float(row["furnace_bath_temp"]),
                float(row["wall_panel_temp"]), float(row["electrode_temp"]),
                float(row["cooling_water_outlet_temp"]), float(row["power_factor"]),
                float(row["energy_this_heat_kwh"]), float(row["electrode_consumption_kg"]),
                float(row["grid_frequency"]),
            ], dtype=np.float32)
            a_window = np.roll(a_window, -1, axis=1)
            a_window[:, -1] = ch_row
            ch_means = anomaly_detector.channel_means[:, None]
            ch_stds = anomaly_detector.channel_stds[:, None] + 1e-6
            normed = (a_window - ch_means) / ch_stds
            cached_anomaly = anomaly_detector.score(normed.astype(np.float32))
        states.append(_state_projection(row, cached_summary, cached_anomaly))
    return states


def _trajectory_quality_score(sub: pd.DataFrame, slice_start: int, length: int) -> float:
    """Higher = the synthetic oracle prefers this trajectory.

    Heuristic combination: penalise wall over-temp and PF deficit, reward
    quality bonus and low backlog.
    """
    t = sub.iloc[slice_start : slice_start + length]
    safety_violations = float((t["wall_panel_temp"] > 240.0).sum())
    pf_violations = float((t["power_factor"] < 0.92).sum())
    quality_steps = float(((t["furnace_bath_temp"] >= 1600.0) & (t["furnace_bath_temp"] <= 1650.0)).sum())
    avg_backlog = float(t["production_backlog"].mean())
    return -3.0 * safety_violations - 1.0 * pf_violations + 1.5 * quality_steps - 2.0 * avg_backlog


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--train", default=str(DEFAULT_DATA_ROOT / "processed" / "train" / "data.parquet"))
    p.add_argument("--val", default=str(DEFAULT_DATA_ROOT / "processed" / "val" / "data.parquet"))
    p.add_argument("--forecaster", default=str(HERE / "models" / "forecaster" / "v0.1.0"))
    p.add_argument("--anomaly", default=str(HERE / "models" / "anomaly" / "v0.1.0"))
    p.add_argument("--n-pairs", type=int, default=200)
    p.add_argument("--traj-len", type=int, default=TRAJ_LEN)
    p.add_argument("--epochs", type=int, default=20)
    p.add_argument("--batch", type=int, default=16)
    p.add_argument("--lr", type=float, default=1e-3)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--out", default=str(HERE / "models" / "reward_model" / "v0.1.0"))
    p.add_argument("--prefs-out",
                   default=str(DEFAULT_DATA_ROOT / "preferences" / "oracle_v1.jsonl"))
    args = p.parse_args()

    torch.manual_seed(args.seed)
    rng = np.random.default_rng(args.seed)

    from forecaster.lstm_forecaster import load_forecaster
    from anomaly.autoencoder import load_anomaly_detector
    forecaster = load_forecaster(args.forecaster)
    anomaly_det = load_anomaly_detector(args.anomaly)
    print(f"[reward] M2 + M3 loaded")

    train_df = pd.read_parquet(args.train)
    train_df = train_df.sort_values(["episode_id", "step_id"]).reset_index(drop=True)
    episodes = sorted(train_df["episode_id"].unique().tolist())
    print(f"[reward] train episodes: {len(episodes)}")

    # Pre-compute the 23-D state sequences per episode.
    print("[reward] replaying episodes through M2/M3 ...")
    ep_states: dict[int, np.ndarray] = {}
    ep_actions: dict[int, np.ndarray] = {}
    ep_frames: dict[int, pd.DataFrame] = {}
    for ep_id, sub in train_df.groupby("episode_id"):
        states = _replay_episode(sub, forecaster, anomaly_det)
        ep_states[ep_id] = np.stack(states, axis=0).astype(np.float32)
        ep_actions[ep_id] = sub.sort_values("step_id")["action_id"].to_numpy(dtype=np.int64)
        ep_frames[ep_id] = sub.sort_values("step_id").reset_index(drop=True)
    print(f"[reward] cached {len(ep_states)} episode state arrays")

    # Sample pairs: pick two random (episode, slice_start) windows, label by oracle.
    pairs: list[tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, int]] = []
    audit: list[dict] = []
    n_attempts = 0
    while len(pairs) < args.n_pairs and n_attempts < args.n_pairs * 10:
        n_attempts += 1
        ep_a, ep_b = rng.choice(episodes, size=2, replace=True)
        st_a = ep_states[ep_a]; ac_a = ep_actions[ep_a]
        st_b = ep_states[ep_b]; ac_b = ep_actions[ep_b]
        if len(st_a) <= args.traj_len or len(st_b) <= args.traj_len:
            continue
        sa = int(rng.integers(0, len(st_a) - args.traj_len))
        sb = int(rng.integers(0, len(st_b) - args.traj_len))
        score_a = _trajectory_quality_score(ep_frames[ep_a], sa, args.traj_len)
        score_b = _trajectory_quality_score(ep_frames[ep_b], sb, args.traj_len)
        if abs(score_a - score_b) < 1e-3:
            continue  # skip ties
        label = 1 if score_a > score_b else 0
        pairs.append((
            st_a[sa : sa + args.traj_len], ac_a[sa : sa + args.traj_len],
            st_b[sb : sb + args.traj_len], ac_b[sb : sb + args.traj_len],
            label,
        ))
        audit.append({
            "episode_a": int(ep_a), "start_a": sa, "score_a": float(score_a),
            "episode_b": int(ep_b), "start_b": sb, "score_b": float(score_b),
            "label": label,
        })
    print(f"[reward] sampled {len(pairs)} preference pairs ({n_attempts} attempts)")
    if len(pairs) < 10:
        raise SystemExit("[reward] not enough non-tied pairs -- check oracle scoring or collect more data")

    # Persist audit trail.
    prefs_out = Path(args.prefs_out)
    prefs_out.parent.mkdir(parents=True, exist_ok=True)
    with open(prefs_out, "w") as f:
        for rec in audit:
            f.write(json.dumps(rec) + "\n")
    print(f"[reward] audit -> {prefs_out}")

    # Stack into tensors.
    A_states = torch.from_numpy(np.stack([p[0] for p in pairs])).float()
    A_acts   = torch.from_numpy(np.stack([p[1] for p in pairs])).long()
    B_states = torch.from_numpy(np.stack([p[2] for p in pairs])).float()
    B_acts   = torch.from_numpy(np.stack([p[3] for p in pairs])).long()
    labels   = torch.from_numpy(np.asarray([p[4] for p in pairs], dtype=np.float32))

    # Per-feature normalisation across the union of A and B states.
    flat = torch.cat([A_states.reshape(-1, REWARD_STATE_DIM), B_states.reshape(-1, REWARD_STATE_DIM)], dim=0)
    state_means = flat.mean(dim=0)
    state_stds = flat.std(dim=0) + 1e-6
    A_states = (A_states - state_means) / state_stds
    B_states = (B_states - state_means) / state_stds

    n = len(pairs)
    n_train = int(n * 0.85)
    perm = torch.randperm(n)
    train_idx, val_idx = perm[:n_train], perm[n_train:]

    model = PrefRewardModel(state_dim=REWARD_STATE_DIM, n_actions=N_ACTIONS)
    optim = torch.optim.Adam(model.parameters(), lr=args.lr)
    bce = nn.BCEWithLogitsLoss()

    for ep in range(args.epochs):
        model.train()
        ep_loss = 0.0
        ep_correct = 0
        idx_perm = train_idx[torch.randperm(len(train_idx))]
        for i in range(0, len(idx_perm), args.batch):
            ix = idx_perm[i : i + args.batch]
            logit = model((A_states[ix], A_acts[ix]), (B_states[ix], B_acts[ix]))
            loss = bce(logit, labels[ix])
            optim.zero_grad()
            loss.backward()
            optim.step()
            ep_loss += float(loss) * len(ix)
            ep_correct += int(((logit > 0).float() == labels[ix]).sum())
        model.eval()
        with torch.no_grad():
            val_logit = model((A_states[val_idx], A_acts[val_idx]), (B_states[val_idx], B_acts[val_idx]))
            val_acc = float(((val_logit > 0).float() == labels[val_idx]).float().mean())
        print(f"[reward] epoch {ep+1:2d}/{args.epochs}  loss={ep_loss/len(train_idx):.4f}  "
              f"train_acc={ep_correct/len(train_idx):.3f}  val_acc={val_acc:.3f}")

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    torch.save(model.state_dict(), out_dir / "reward_model.pt")
    with open(out_dir / "meta.json", "w") as f:
        json.dump({
            "state_dim": REWARD_STATE_DIM,
            "n_actions": N_ACTIONS,
            "state_means": state_means.tolist(),
            "state_stds": state_stds.tolist(),
            "n_pairs": n,
            "traj_len": args.traj_len,
            "oracle": "synthetic_v1: -3*wall_violations - 1*pf_deficit + 1.5*quality - 2*avg_backlog",
        }, f, indent=2)
    print(f"[reward] saved -> {out_dir}")


if __name__ == "__main__":
    main()
