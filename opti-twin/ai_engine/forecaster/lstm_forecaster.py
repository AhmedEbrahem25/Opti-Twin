"""Tariff & demand forecaster (M2, planing-v2.md §6).

Inputs (60-tick = 3 sim-min lookback):
    [electricity_price, arc_power_mw, is_peak, tou_mode,
     sim_hour_sin, sim_hour_cos, grid_frequency]   (7 features)

Outputs:
    price quantiles    : (B, 600, 6)  -> mean + p05/p25/p50/p75/p95
    expected load      : (B, 600)     -> MW

Inference-time policy obs needs a fixed-size summary (planing-v2.md §5.3
"Forecast (M2) -- 5 quantiles + 1 horizon-mean -> 6"). `summarise_for_obs`
returns that 6-D vector.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Tuple

import numpy as np
import torch
import torch.nn as nn

# Note: planing-v2.md §6.1 specifies a 60-tick lookback and 600-tick horizon under
# the implicit assumption of 3-second ticks (lookback 3 min, horizon 30 min). Our
# env runs at 3-sim-min per step (`environment.SIM_MIN_PER_STEP`) so we scale
# both ends down: 30 ticks ≈ 1.5 sim-h history, 60 ticks ≈ 3 sim-h forward —
# enough lead time for pre-peak shifting + fits comfortably in a 480-step episode.
LOOKBACK = 30
FORECAST_HORIZON = 60
QUANTILES = (0.05, 0.25, 0.50, 0.75, 0.95)
N_PRICE_OUTPUTS = len(QUANTILES) + 1               # quantiles + mean
N_INPUT_FEATURES = 7
OBS_SUMMARY_DIM = 6                                # 5 quantiles + horizon mean


class TariffLoadForecaster(nn.Module):
    def __init__(
        self,
        input_dim: int = N_INPUT_FEATURES,
        hidden: int = 128,
        horizon: int = FORECAST_HORIZON,
        n_price_outputs: int = N_PRICE_OUTPUTS,
    ) -> None:
        super().__init__()
        self.input_dim = input_dim
        self.hidden = hidden
        self.horizon = horizon
        self.n_price_outputs = n_price_outputs
        self.encoder = nn.LSTM(input_dim, hidden, batch_first=True)
        self.price_head = nn.Linear(hidden, horizon * n_price_outputs)
        self.load_head = nn.Linear(hidden, horizon)

    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        # x: (B, LOOKBACK, input_dim)
        _, (h, _) = self.encoder(x)
        h = h[-1]  # (B, hidden)
        price = self.price_head(h).view(-1, self.horizon, self.n_price_outputs)
        load = self.load_head(h)
        return price, load


@dataclass
class Forecaster:
    """Wraps a trained TariffLoadForecaster + per-feature normalisation stats."""
    model: TariffLoadForecaster
    feature_means: np.ndarray  # (input_dim,)
    feature_stds: np.ndarray   # (input_dim,)
    feature_columns: list[str]

    @torch.no_grad()
    def predict(self, lookback_window: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Return (price_quantiles, load_mean) for one (LOOKBACK, F) window."""
        if lookback_window.shape != (LOOKBACK, self.model.input_dim):
            raise ValueError(
                f"expected ({LOOKBACK}, {self.model.input_dim}); got {lookback_window.shape}"
            )
        x = (lookback_window - self.feature_means[None, :]) / self.feature_stds[None, :]
        x_t = torch.from_numpy(x.astype(np.float32)).unsqueeze(0)
        price, load = self.model(x_t)
        return price.squeeze(0).cpu().numpy(), load.squeeze(0).cpu().numpy()


def summarise_for_obs(price_quantiles: np.ndarray) -> np.ndarray:
    """Reduce a (HORIZON, n_outputs) price prediction to a 6-D summary for the
    policy observation: median at +30min, +60min, plus p05/p95 at +30min and the
    horizon mean. Inputs out of bounds are clamped.
    """
    h = price_quantiles.shape[0]
    p_mid = h // 4 if h >= 4 else 0   # ~30 min into the 30-min horizon (mid)
    p_end = min(h - 1, p_mid * 2)
    # Quantile column indices in price_quantiles last dim:
    #   0=mean, 1=p05, 2=p25, 3=p50, 4=p75, 5=p95
    median_30 = float(price_quantiles[p_mid, 3])
    median_60 = float(price_quantiles[p_end, 3])
    p05_30 = float(price_quantiles[p_mid, 1])
    p95_30 = float(price_quantiles[p_mid, 5])
    horizon_mean = float(price_quantiles[:, 0].mean())
    interval_width = float(p95_30 - p05_30)
    return np.array([median_30, median_60, p05_30, p95_30, horizon_mean, interval_width],
                    dtype=np.float32)


def pinball_loss(
    y_true: torch.Tensor,
    y_pred_quantiles: torch.Tensor,
    quantiles: Tuple[float, ...] = QUANTILES,
) -> torch.Tensor:
    """Pinball/quantile loss. y_pred_quantiles columns: (mean, q1, q2, ..., qK).
    The mean column is supervised separately by MSE in the trainer.
    """
    losses = []
    for i, q in enumerate(quantiles):
        diff = y_true - y_pred_quantiles[..., i + 1]  # +1 to skip the mean column
        losses.append(torch.maximum(q * diff, (q - 1.0) * diff))
    return torch.mean(torch.stack(losses, dim=0))


def load_forecaster(model_dir: str | Path) -> Forecaster:
    model_dir = Path(model_dir)
    with open(model_dir / "feature_columns.json") as f:
        meta = json.load(f)
    model = TariffLoadForecaster(
        input_dim=int(meta.get("input_dim", N_INPUT_FEATURES)),
        hidden=int(meta.get("hidden", 128)),
        horizon=int(meta.get("horizon", FORECAST_HORIZON)),
        n_price_outputs=int(meta.get("n_price_outputs", N_PRICE_OUTPUTS)),
    )
    model.load_state_dict(torch.load(model_dir / "forecaster.pt", map_location="cpu"))
    model.eval()
    return Forecaster(
        model=model,
        feature_means=np.array(meta["feature_means"], dtype=np.float32),
        feature_stds=np.array(meta["feature_stds"], dtype=np.float32),
        feature_columns=list(meta["feature_columns"]),
    )
