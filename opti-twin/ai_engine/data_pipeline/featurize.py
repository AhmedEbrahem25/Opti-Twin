"""Featurise raw transition Parquet -> processed Parquet ready for training.

Adds:
  - rolling means (5/15/30 min lookback) for arc_power_mw, wall_panel_temp,
    electricity_price — useful for the M2 forecaster and PPO obs warmup.
  - lag features price_t-{1..60} for forecasting input windows.
  - sim_hour sin/cos encoding for the M2 forecaster input.
  - per-column StandardScaler (fit on train, applied to all splits).

The scaler is persisted as joblib so inference reproduces the exact transform.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Iterable, List

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import joblib
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler

# `ai_engine/data_pipeline/featurize.py` -> up two levels reaches `opti-twin/`.
DEFAULT_DATA_ROOT = HERE.parent.parent / "data"

# Channels that get rolling-mean derivatives. Step is 3 sim-min, so the
# windows below correspond to 5/15/30 sim-min lookback.
ROLLING_CHANNELS = ["arc_power_mw", "wall_panel_temp", "electricity_price"]
ROLLING_WINDOWS = {"5min": 2, "15min": 5, "30min": 10}

LAG_FEATURE_COL = "electricity_price"
LAG_HORIZON = 60  # 60 ticks = 3 sim-min lookback (matches M2 input window)

# Columns that the StandardScaler should normalise. Keeps booleans / IDs out.
SCALER_COLUMNS: List[str] = [
    "arc_power_mw",
    "furnace_bath_temp",
    "wall_panel_temp",
    "electrode_temp",
    "cooling_water_outlet_temp",
    "heat_progress_pct",
    "current_batch_weight",
    "batches_today",
    "production_backlog",
    "power_factor",
    "energy_this_heat_kwh",
    "electrode_position_mm",
    "electrode_consumption_kg",
    "electricity_price",
    "grid_frequency",
]


def _add_rolling(df: pd.DataFrame) -> pd.DataFrame:
    df = df.sort_values(["episode_id", "step_id"]).reset_index(drop=True)
    grouped = df.groupby("episode_id", group_keys=False)
    for col in ROLLING_CHANNELS:
        for tag, w in ROLLING_WINDOWS.items():
            df[f"{col}_roll_{tag}"] = grouped[col].transform(
                lambda s: s.rolling(window=w, min_periods=1).mean()
            )
    return df


def _add_lag(df: pd.DataFrame) -> pd.DataFrame:
    df = df.sort_values(["episode_id", "step_id"]).reset_index(drop=True)
    grouped = df.groupby("episode_id", group_keys=False)
    for k in range(1, LAG_HORIZON + 1):
        df[f"{LAG_FEATURE_COL}_lag_{k}"] = grouped[LAG_FEATURE_COL].shift(k)
    return df


def _add_sim_hour_encoding(df: pd.DataFrame) -> pd.DataFrame:
    rad = 2.0 * np.pi * df["sim_hour"] / 24.0
    df["sim_hour_sin"] = np.sin(rad)
    df["sim_hour_cos"] = np.cos(rad)
    return df


def featurize_frame(df: pd.DataFrame) -> pd.DataFrame:
    df = _add_rolling(df)
    df = _add_lag(df)
    df = _add_sim_hour_encoding(df)
    return df


def fit_scaler(train_df: pd.DataFrame, columns: Iterable[str] = SCALER_COLUMNS) -> StandardScaler:
    scaler = StandardScaler()
    scaler.fit(train_df[list(columns)].to_numpy(dtype=float))
    scaler.feature_names_in_ = np.array(list(columns))
    return scaler


def apply_scaler(df: pd.DataFrame, scaler: StandardScaler) -> pd.DataFrame:
    cols = list(scaler.feature_names_in_)
    df = df.copy()
    df[[f"{c}_scaled" for c in cols]] = scaler.transform(df[cols].to_numpy(dtype=float))
    return df


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--raw-root", default=str(DEFAULT_DATA_ROOT / "raw"))
    p.add_argument("--out-root", default=str(DEFAULT_DATA_ROOT / "processed"))
    p.add_argument("--scaler-out", default=str(DEFAULT_DATA_ROOT / "scalers" / "scaler_v1.joblib"))
    args = p.parse_args()

    raw_root = Path(args.raw_root)
    out_root = Path(args.out_root)
    scaler_path = Path(args.scaler_out)

    parquets = sorted(raw_root.rglob("episode_*.parquet"))
    if not parquets:
        raise SystemExit(f"[featurize] no episode parquet files under {raw_root}")
    print(f"[featurize] loading {len(parquets)} episodes from {raw_root}")
    df = pd.concat([pd.read_parquet(p) for p in parquets], ignore_index=True)
    print(f"[featurize] {len(df)} rows total before featurisation")

    df = featurize_frame(df)
    print(f"[featurize] columns after featurise: {len(df.columns)}")

    scaler_path.parent.mkdir(parents=True, exist_ok=True)
    out_root.mkdir(parents=True, exist_ok=True)

    out_path = out_root / "all_featurised.parquet"
    df.to_parquet(out_path, index=False)
    print(f"[featurize] wrote {out_path}")

    # Note: the actual train-only scaler fit happens after split.py runs. This
    # script's --scaler-out path is just where split.py will deposit it.
    print(f"[featurize] scaler will be fit on the train split by split.py -> {scaler_path}")


if __name__ == "__main__":
    main()
