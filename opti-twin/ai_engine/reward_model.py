"""M5 preference reward model (planing-v2.md §9).

Bradley-Terry pairwise preference learner. Trained on (trajectory_a,
trajectory_b, label) tuples where label=1 means A is preferred. Each
trajectory is a fixed-length sequence of (state, action) pairs; the model
predicts a per-step scalar reward, sums them, and the pairwise sigmoid is
trained against the binary preference label.

The reward model takes a *semantic* state projection (telemetry + 6 forecast
+ 1 anomaly = 23-D), not the full 39-D PPO obs — pricing dims correlate
strongly with the forecast and would inflate parameters.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Tuple

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

from environment import ACTIONS

REWARD_STATE_DIM = 23  # 16 telemetry + 6 forecast + 1 anomaly
N_ACTIONS = len(ACTIONS)


class PrefRewardModel(nn.Module):
    def __init__(self, state_dim: int = REWARD_STATE_DIM, n_actions: int = N_ACTIONS) -> None:
        super().__init__()
        self.state_dim = state_dim
        self.n_actions = n_actions
        self.net = nn.Sequential(
            nn.Linear(state_dim + n_actions, 128), nn.ReLU(),
            nn.Linear(128, 64), nn.ReLU(),
            nn.Linear(64, 1),
        )

    def per_step_reward(self, states: torch.Tensor, actions: torch.Tensor) -> torch.Tensor:
        """states: (B, T, state_dim)  actions: (B, T) int64."""
        a_oh = F.one_hot(actions, num_classes=self.n_actions).float()  # (B, T, n_actions)
        x = torch.cat([states, a_oh], dim=-1)
        return self.net(x).squeeze(-1)  # (B, T)

    def trajectory_reward(self, states: torch.Tensor, actions: torch.Tensor) -> torch.Tensor:
        """Sum per-step rewards over time. Returns (B,)."""
        return self.per_step_reward(states, actions).sum(dim=1)

    def forward(self, traj_a: Tuple[torch.Tensor, torch.Tensor],
                traj_b: Tuple[torch.Tensor, torch.Tensor]) -> torch.Tensor:
        ra = self.trajectory_reward(*traj_a)
        rb = self.trajectory_reward(*traj_b)
        # Sigmoid is applied inside BCEWithLogitsLoss for numerical stability.
        return ra - rb


@dataclass
class RewardModelBundle:
    model: PrefRewardModel
    state_means: np.ndarray
    state_stds: np.ndarray

    def normalise(self, state_arr: np.ndarray) -> np.ndarray:
        return (state_arr - self.state_means) / (self.state_stds + 1e-6)


def load_reward_model(model_dir: str | Path) -> RewardModelBundle:
    model_dir = Path(model_dir)
    with open(model_dir / "meta.json") as f:
        meta = json.load(f)
    model = PrefRewardModel(
        state_dim=int(meta["state_dim"]),
        n_actions=int(meta["n_actions"]),
    )
    model.load_state_dict(torch.load(model_dir / "reward_model.pt", map_location="cpu"))
    model.eval()
    return RewardModelBundle(
        model=model,
        state_means=np.array(meta["state_means"], dtype=np.float32),
        state_stds=np.array(meta["state_stds"], dtype=np.float32),
    )
