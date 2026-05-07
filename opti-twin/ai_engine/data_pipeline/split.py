"""Stratified train/val/test split (planing-v2.md §3.3).

Splits at the episode level (no leakage), stratified by `difficulty`.
Default ratios: 70/15/15. Eval-scenario seeds are already excluded by
`collect_episodes.py:_bump_past_eval_seeds`, so this script just partitions
whatever made it into raw/.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Iterable

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import joblib
import numpy as np
import pandas as pd

from data_pipeline.featurize import (
    DEFAULT_DATA_ROOT,
    SCALER_COLUMNS,
    apply_scaler,
    featurize_frame,
    fit_scaler,
)


def stratified_episode_split(
    df: pd.DataFrame,
    *,
    train_frac: float,
    val_frac: float,
    seed: int,
) -> dict:
    """Return {'train': df, 'val': df, 'test': df} keyed by partition."""
    rng = np.random.default_rng(seed)
    parts: dict[str, list[pd.DataFrame]] = {"train": [], "val": [], "test": []}
    for difficulty, sub in df.groupby("difficulty"):
        episodes = sorted(sub["episode_id"].unique().tolist())
        rng.shuffle(episodes)
        n = len(episodes)
        n_train = int(round(n * train_frac))
        n_val = int(round(n * val_frac))
        train_eps = set(episodes[:n_train])
        val_eps = set(episodes[n_train : n_train + n_val])
        test_eps = set(episodes[n_train + n_val :])
        parts["train"].append(sub[sub["episode_id"].isin(train_eps)])
        parts["val"].append(sub[sub["episode_id"].isin(val_eps)])
        parts["test"].append(sub[sub["episode_id"].isin(test_eps)])
        print(
            f"[split] difficulty={difficulty}  train={len(train_eps)}  "
            f"val={len(val_eps)}  test={len(test_eps)} (of {n})"
        )
    return {k: pd.concat(v, ignore_index=True) for k, v in parts.items()}


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--raw-root", default=str(DEFAULT_DATA_ROOT / "raw"))
    p.add_argument("--out-root", default=str(DEFAULT_DATA_ROOT / "processed"))
    p.add_argument("--scaler-out", default=str(DEFAULT_DATA_ROOT / "scalers" / "scaler_v1.joblib"))
    p.add_argument("--train", type=float, default=0.70)
    p.add_argument("--val", type=float, default=0.15)
    p.add_argument("--seed", type=int, default=2026)
    args = p.parse_args()

    raw_root = Path(args.raw_root)
    out_root = Path(args.out_root)
    scaler_path = Path(args.scaler_out)

    parquets = sorted(raw_root.rglob("episode_*.parquet"))
    if not parquets:
        raise SystemExit(f"[split] no episode parquet files under {raw_root}")
    print(f"[split] loading {len(parquets)} episodes")
    df = pd.concat([pd.read_parquet(p) for p in parquets], ignore_index=True)
    df = featurize_frame(df)

    parts = stratified_episode_split(df, train_frac=args.train, val_frac=args.val, seed=args.seed)

    print(f"[split] fitting scaler on train ({len(parts['train'])} rows)")
    scaler = fit_scaler(parts["train"], columns=SCALER_COLUMNS)

    scaler_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(scaler, scaler_path)
    print(f"[split] saved scaler -> {scaler_path}")

    for name, part in parts.items():
        part_dir = out_root / name
        part_dir.mkdir(parents=True, exist_ok=True)
        scaled = apply_scaler(part, scaler)
        out_path = part_dir / "data.parquet"
        scaled.to_parquet(out_path, index=False)
        print(f"[split] wrote {name}/{out_path.name}  rows={len(scaled)}")


if __name__ == "__main__":
    main()
