"""
Train the Opti-Twin PPO policy.

Pipeline:
  1. Roll out the scripted policy (`agent.OptiTwinAgent._scripted_policy`) over
     the env to collect ~50K (obs, action) pairs.
  2. Train an MLP classifier (the "BC warm start") to imitate that scripted
     policy. ~10 epochs; ~2 min on CPU.
  3. Initialise a Stable-Baselines3 PPO agent and copy the BC-trained weights
     into its policy network.
  4. Fine-tune with PPO on the same env for `--total-timesteps` steps.
  5. Save final model to `models/opti_twin_ppo.zip`.

Usage:
    python train_ppo.py                       # defaults: 200K timesteps, seed 42
    python train_ppo.py --total-timesteps 50000 --bc-pairs 10000   # quick run
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import List, Tuple

import gymnasium as gym
import numpy as np
import torch
import torch.nn as nn
from stable_baselines3 import PPO
from stable_baselines3.common.monitor import Monitor

# Local imports from this directory
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from agent import OptiTwinAgent
from environment import ACTIONS, OBS_DIM, OptiTwinEAFEnv, make_obs_vector


def collect_bc_dataset(n_pairs: int, seed: int) -> Tuple[np.ndarray, np.ndarray]:
    """Roll out the scripted policy, return (obs[N,32], actions[N])."""
    teacher = OptiTwinAgent(model_path=None)  # forces scripted fallback
    env = OptiTwinEAFEnv()
    obs_buf: List[np.ndarray] = []
    act_buf: List[int] = []

    obs, _ = env.reset(seed=seed)
    while len(obs_buf) < n_pairs:
        label = teacher._scripted_policy(env._state)
        if label not in ACTIONS:
            # Scripted policy can emit labels the env doesn't simulate (e.g. in
            # legacy code paths). Map to the safest fallback.
            label = "HOLD_STEADY"
        action_id = ACTIONS.index(label)
        obs_buf.append(obs.copy())
        act_buf.append(action_id)
        obs, _, terminated, truncated, _ = env.step(action_id)
        if terminated or truncated:
            obs, _ = env.reset(seed=seed + len(obs_buf))

    return np.asarray(obs_buf, dtype=np.float32), np.asarray(act_buf, dtype=np.int64)


class BCNet(nn.Module):
    """MLP matching SB3 default MlpPolicy net_arch (pi=[64,64])."""

    def __init__(self, obs_dim: int, n_actions: int) -> None:
        super().__init__()
        self.shared = nn.Sequential(
            nn.Linear(obs_dim, 64),
            nn.Tanh(),
            nn.Linear(64, 64),
            nn.Tanh(),
        )
        self.head = nn.Linear(64, n_actions)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.head(self.shared(x))


def train_bc(obs: np.ndarray, actions: np.ndarray, *, epochs: int, batch_size: int, lr: float) -> BCNet:
    net = BCNet(OBS_DIM, len(ACTIONS))
    optim = torch.optim.Adam(net.parameters(), lr=lr)
    loss_fn = nn.CrossEntropyLoss()
    obs_t = torch.from_numpy(obs)
    act_t = torch.from_numpy(actions)
    n = len(obs)
    print(f"[BC] training on {n} pairs, {epochs} epochs, batch={batch_size}")
    for ep in range(epochs):
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
        print(f"[BC] epoch {ep+1:2d}/{epochs}  loss={ep_loss / n:.4f}  acc={ep_correct / n:.3f}")
    return net


def init_ppo_from_bc(ppo: PPO, bc: BCNet) -> None:
    """Copy BC MLP weights into PPO's MlpPolicy (matches default net_arch)."""
    policy_state = ppo.policy.state_dict()
    bc_state = bc.state_dict()

    # SB3 MlpPolicy default architecture mapping:
    #   policy.mlp_extractor.policy_net.0.{weight,bias}  <- bc.shared.0.*
    #   policy.mlp_extractor.policy_net.2.{weight,bias}  <- bc.shared.2.*
    #   policy.action_net.{weight,bias}                  <- bc.head.*
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
        if ppo_key in policy_state and bc_key in bc_state and policy_state[ppo_key].shape == bc_state[bc_key].shape:
            policy_state[ppo_key] = bc_state[bc_key].clone()
            copied += 1
        else:
            print(f"[BC->PPO] skipped {bc_key} -> {ppo_key} (shape mismatch or missing)")
    ppo.policy.load_state_dict(policy_state)
    print(f"[BC->PPO] copied {copied}/{len(mapping)} tensors into PPO policy")


class _GymCompat(gym.Env):
    """Subclass gymnasium.Env so SB3's DummyVecEnv wrapper finds the expected attributes."""

    metadata = {"render_modes": []}

    def __init__(self, weights=None) -> None:
        super().__init__()
        self._env = OptiTwinEAFEnv(weights)
        self.observation_space = self._env.observation_space
        self.action_space = self._env.action_space
        self.render_mode = None

    def reset(self, *, seed=None, options=None):
        return self._env.reset(seed=seed, options=options)

    def step(self, action):
        return self._env.step(int(action))


def _make_env(weights=None):
    return Monitor(_GymCompat(weights))


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--total-timesteps", type=int, default=200_000)
    p.add_argument("--bc-pairs", type=int, default=50_000)
    p.add_argument("--bc-epochs", type=int, default=10)
    p.add_argument("--bc-batch", type=int, default=256)
    p.add_argument("--bc-lr", type=float, default=3e-4)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--output", default=str(HERE / "models" / "opti_twin_ppo.zip"))
    args = p.parse_args()

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    torch.manual_seed(args.seed)
    np.random.seed(args.seed)

    print(f"[opti-twin] training PPO  seed={args.seed}  out={out_path}")

    # 1+2. BC warm start
    print(f"[step 1/4] collecting {args.bc_pairs} scripted-policy rollouts...")
    obs, acts = collect_bc_dataset(args.bc_pairs, seed=args.seed)
    print(f"[step 1/4] action distribution:")
    for i, lab in enumerate(ACTIONS):
        n = int((acts == i).sum())
        print(f"           {lab:<22} {n:6d}  ({n/len(acts)*100:.1f}%)")

    print(f"[step 2/4] training BC MLP...")
    bc_net = train_bc(obs, acts, epochs=args.bc_epochs, batch_size=args.bc_batch, lr=args.bc_lr)

    # 3. Init PPO and inject BC weights
    print(f"[step 3/4] initialising PPO and copying BC weights...")
    env = _make_env()
    ppo = PPO(
        "MlpPolicy",
        env,
        learning_rate=3e-4,
        n_steps=2048,
        batch_size=64,
        n_epochs=10,
        gamma=0.99,
        ent_coef=0.01,
        clip_range=0.2,
        seed=args.seed,
        verbose=0,
    )
    init_ppo_from_bc(ppo, bc_net)

    # 4. PPO fine-tune
    print(f"[step 4/4] fine-tuning PPO for {args.total_timesteps} timesteps...")
    ppo.learn(total_timesteps=args.total_timesteps, progress_bar=False)

    ppo.save(str(out_path))
    print(f"[done] saved PPO model to {out_path}")


if __name__ == "__main__":
    main()
