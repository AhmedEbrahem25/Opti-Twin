"""Telemetry autoencoder for anomaly detection (M3, planing-v2.md §7.2).

Reconstructs a 60-tick window of 9 thermal/electrical channels. The
reconstruction error is mapped through a calibrated threshold to an
anomaly score in [0, 1] suitable for direct insertion into the policy obs.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import numpy as np
import torch
import torch.nn as nn

WINDOW_LEN = 60
N_CHANNELS = 9
LATENT_DIM = 8


class TelemetryAutoencoder(nn.Module):
    def __init__(self, channels: int = N_CHANNELS, window: int = WINDOW_LEN, latent: int = LATENT_DIM) -> None:
        super().__init__()
        self.channels = channels
        self.window = window
        self.latent = latent
        self.encoder = nn.Sequential(
            nn.Conv1d(channels, 32, kernel_size=5, padding=2), nn.ReLU(),
            nn.MaxPool1d(2),
            nn.Conv1d(32, 64, kernel_size=3, padding=1), nn.ReLU(),
            nn.MaxPool1d(2),
            nn.Flatten(),
            nn.Linear(64 * (window // 4), latent),
        )
        self.decoder = nn.Sequential(
            nn.Linear(latent, 64 * (window // 4)),
            nn.Unflatten(1, (64, window // 4)),
            nn.Upsample(scale_factor=2),
            nn.Conv1d(64, 32, kernel_size=3, padding=1), nn.ReLU(),
            nn.Upsample(scale_factor=2),
            nn.Conv1d(32, channels, kernel_size=5, padding=2),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.decoder(self.encoder(x))

    @torch.no_grad()
    def reconstruction_error(self, x: torch.Tensor) -> torch.Tensor:
        recon = self.forward(x)
        per_channel = torch.mean((recon - x) ** 2, dim=2)  # (B, C)
        return torch.mean(per_channel, dim=1)              # (B,)


@dataclass
class AnomalyDetector:
    """Wraps a trained autoencoder + calibrated threshold for inference."""
    model: TelemetryAutoencoder
    threshold: float
    channel_means: np.ndarray  # (C,) — for missing-window padding fallback
    channel_stds: np.ndarray   # (C,)

    @torch.no_grad()
    def score(self, window: np.ndarray) -> float:
        """Return an anomaly score in [0, 1] for one (C, T) window."""
        if window.shape != (self.model.channels, self.model.window):
            raise ValueError(f"expected ({self.model.channels}, {self.model.window}); got {window.shape}")
        x = torch.from_numpy(window.astype(np.float32)).unsqueeze(0)
        err = float(self.model.reconstruction_error(x).item())
        if self.threshold <= 0.0:
            return 0.0
        return float(np.clip(err / self.threshold, 0.0, 1.0))


def load_anomaly_detector(model_dir: str | Path) -> AnomalyDetector:
    model_dir = Path(model_dir)
    model = TelemetryAutoencoder()
    state_dict = torch.load(model_dir / "autoencoder.pt", map_location="cpu")
    model.load_state_dict(state_dict)
    model.eval()
    with open(model_dir / "threshold.json") as f:
        meta = json.load(f)
    return AnomalyDetector(
        model=model,
        threshold=float(meta["threshold"]),
        channel_means=np.array(meta["channel_means"], dtype=np.float32),
        channel_stds=np.array(meta["channel_stds"], dtype=np.float32),
    )
