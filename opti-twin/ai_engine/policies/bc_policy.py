"""Behaviour-cloning MLP and PPO weight-transfer (planing-v2.md §8).

Extracted from `train_ppo.py` so M4 has a standalone trainer (`train_bc.py`)
and the same policy can be re-used to warm-start any future PPO run.

The architecture mirrors SB3's default `MlpPolicy(net_arch=[64,64], Tanh)` so
weights copy directly with no projection layer.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import torch
import torch.nn as nn


class BCNet(nn.Module):
    """MLP matching SB3 default MlpPolicy (pi=[64,64], Tanh)."""

    def __init__(self, obs_dim: int, n_actions: int) -> None:
        super().__init__()
        self.obs_dim = obs_dim
        self.n_actions = n_actions
        self.shared = nn.Sequential(
            nn.Linear(obs_dim, 64),
            nn.Tanh(),
            nn.Linear(64, 64),
            nn.Tanh(),
        )
        self.head = nn.Linear(64, n_actions)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.head(self.shared(x))


def load_bc_net(path: str | Path, *, obs_dim: int, n_actions: int) -> BCNet:
    net = BCNet(obs_dim=obs_dim, n_actions=n_actions)
    state = torch.load(path, map_location="cpu")
    net.load_state_dict(state)
    net.eval()
    return net


def init_ppo_from_bc(ppo, bc: BCNet) -> int:
    """Copy BC MLP weights into a freshly-constructed SB3 PPO policy.

    Returns the number of tensors successfully copied. Skips silently when
    shapes mismatch — useful when the obs space has changed between BC and PPO.
    """
    policy_state = ppo.policy.state_dict()
    bc_state = bc.state_dict()

    mapping = {
        "shared.0.weight": "mlp_extractor.policy_net.0.weight",
        "shared.0.bias":   "mlp_extractor.policy_net.0.bias",
        "shared.2.weight": "mlp_extractor.policy_net.2.weight",
        "shared.2.bias":   "mlp_extractor.policy_net.2.bias",
        "head.weight":     "action_net.weight",
        "head.bias":       "action_net.bias",
    }
    copied = 0
    for bc_key, ppo_key in mapping.items():
        if (
            ppo_key in policy_state
            and bc_key in bc_state
            and policy_state[ppo_key].shape == bc_state[bc_key].shape
        ):
            policy_state[ppo_key] = bc_state[bc_key].clone()
            copied += 1
        else:
            print(f"[BC->PPO] skipped {bc_key} -> {ppo_key} (shape mismatch or missing)")
    ppo.policy.load_state_dict(policy_state)
    print(f"[BC->PPO] copied {copied}/{len(mapping)} tensors")
    return copied
