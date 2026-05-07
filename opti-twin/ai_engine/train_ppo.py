"""
Train the Opti-Twin PPO policy.

Pipeline:
  1. Load a pre-trained BC warm-start checkpoint (`--bc-init`) produced by
     `train_bc.py`. Falls back to inline scripted-rollout BC behind
     `--legacy-inline-bc` for parity with the pre-Phase-A pipeline.
  2. Initialise a Stable-Baselines3 PPO agent and copy the BC weights into
     its policy network.
  3. Fine-tune with PPO on `OptiTwinEAFEnv` for `--total-timesteps` steps.
  4. Save final model to `--output` (default `models/opti_twin_ppo.zip`).

Usage:
    python train_ppo.py --bc-init models/bc/v0.1.0/bc_init.pt
    python train_ppo.py --legacy-inline-bc --bc-pairs 10000 --total-timesteps 50000
"""

from __future__ import annotations

import argparse
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
from policies.bc_policy import BCNet, init_ppo_from_bc, load_bc_net


def collect_bc_dataset(n_pairs: int, seed: int) -> Tuple[np.ndarray, np.ndarray]:
    """Inline scripted-rollout collection (legacy --legacy-inline-bc path)."""
    teacher = OptiTwinAgent(model_path=None)
    env = OptiTwinEAFEnv()
    obs_buf: List[np.ndarray] = []
    act_buf: List[int] = []

    obs, _ = env.reset(seed=seed)
    while len(obs_buf) < n_pairs:
        label = teacher._scripted_policy(env._state)
        if label not in ACTIONS:
            label = "HOLD_STEADY"
        action_id = ACTIONS.index(label)
        obs_buf.append(obs.copy())
        act_buf.append(action_id)
        obs, _, terminated, truncated, _ = env.step(action_id)
        if terminated or truncated:
            obs, _ = env.reset(seed=seed + len(obs_buf))

    return np.asarray(obs_buf, dtype=np.float32), np.asarray(act_buf, dtype=np.int64)


def train_bc_inline(obs: np.ndarray, actions: np.ndarray, *,
                    epochs: int, batch_size: int, lr: float) -> BCNet:
    net = BCNet(OBS_DIM, len(ACTIONS))
    optim = torch.optim.Adam(net.parameters(), lr=lr)
    loss_fn = nn.CrossEntropyLoss()
    obs_t = torch.from_numpy(obs)
    act_t = torch.from_numpy(actions)
    n = len(obs)
    print(f"[BC inline] training on {n} pairs, {epochs} epochs, batch={batch_size}")
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
        print(f"[BC inline] epoch {ep+1:2d}/{epochs}  loss={ep_loss / n:.4f}  acc={ep_correct / n:.3f}")
    return net


class _GymCompat(gym.Env):
    """Subclass gymnasium.Env so SB3's DummyVecEnv wrapper finds the expected attributes."""

    metadata = {"render_modes": []}

    def __init__(self, weights=None, *, forecaster=None, anomaly_detector=None) -> None:
        super().__init__()
        self._env = OptiTwinEAFEnv(
            weights,
            forecaster=forecaster,
            anomaly_detector=anomaly_detector,
        )
        self.observation_space = self._env.observation_space
        self.action_space = self._env.action_space
        self.render_mode = None

    def reset(self, *, seed=None, options=None):
        return self._env.reset(seed=seed, options=options)

    def step(self, action):
        return self._env.step(int(action))


def _make_env(weights=None, *, forecaster=None, anomaly_detector=None):
    return Monitor(_GymCompat(weights, forecaster=forecaster, anomaly_detector=anomaly_detector))


def _eval_policy_quick(ppo: PPO, env, episodes: int = 5) -> float:
    """Quick mean-reward eval on a fresh env. Used by Optuna trial scoring."""
    rewards = []
    for ep in range(episodes):
        obs, _ = env.reset(seed=10_000 + ep)
        total = 0.0
        while True:
            action, _ = ppo.predict(obs, deterministic=True)
            obs, r, term, trunc, _ = env.step(int(action))
            total += float(r)
            if term or trunc:
                break
        rewards.append(total)
    return float(np.mean(rewards))


def run_optuna_study(args, bc_net, forecaster, anomaly_detector) -> dict:
    """Run an Optuna TPE study on a 50K-step proxy task. Returns the best
    hyperparameters as a dict suitable for spreading into PPO(...).
    """
    import optuna
    from policies.bc_policy import init_ppo_from_bc as inject

    def objective(trial: "optuna.Trial") -> float:
        lr = trial.suggest_float("learning_rate", 1e-5, 1e-3, log=True)
        clip = trial.suggest_float("clip_range", 0.1, 0.3)
        ent = trial.suggest_float("ent_coef", 1e-4, 5e-2, log=True)
        gamma = trial.suggest_float("gamma", 0.95, 0.999)
        n_steps = trial.suggest_categorical("n_steps", [1024, 2048, 4096])

        env = _make_env(forecaster=forecaster, anomaly_detector=anomaly_detector)
        ppo = PPO(
            "MlpPolicy", env,
            learning_rate=lr, clip_range=clip, ent_coef=ent,
            gamma=gamma, n_steps=n_steps,
            batch_size=64, n_epochs=10, seed=args.seed, verbose=0,
        )
        inject(ppo, bc_net)
        ppo.learn(total_timesteps=args.tune_budget, progress_bar=False)
        return _eval_policy_quick(ppo, _make_env(
            forecaster=forecaster, anomaly_detector=anomaly_detector,
        ), episodes=3)

    study = optuna.create_study(direction="maximize",
                                 sampler=optuna.samplers.TPESampler(seed=args.seed))
    study.optimize(objective, n_trials=args.tune_trials, show_progress_bar=False)
    print(f"[tune] best value = {study.best_value:.2f}")
    print(f"[tune] best params = {study.best_params}")
    return dict(study.best_params)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--total-timesteps", type=int, default=200_000)
    p.add_argument("--bc-init", default=str(HERE / "models" / "bc" / "v0.2.0" / "bc_init.pt"),
                   help="Path to a BC checkpoint produced by train_bc.py. Use --legacy-inline-bc to bypass.")
    p.add_argument("--forecaster", default=None,
                   help="Path to M2 forecaster directory; populates env obs dims 16-21")
    p.add_argument("--anomaly", default=None,
                   help="Path to M3 anomaly detector directory; populates env obs dim 38")
    p.add_argument("--tune", action="store_true",
                   help="Run Optuna hyperparam search before the final training pass.")
    p.add_argument("--tune-trials", type=int, default=15,
                   help="Number of Optuna trials when --tune is set.")
    p.add_argument("--tune-budget", type=int, default=50_000,
                   help="Steps per trial when --tune is set.")
    p.add_argument("--legacy-inline-bc", action="store_true",
                   help="Run pre-Phase-A inline BC instead of loading a checkpoint.")
    p.add_argument("--bc-pairs", type=int, default=50_000, help="(legacy inline BC only)")
    p.add_argument("--bc-epochs", type=int, default=10, help="(legacy inline BC only)")
    p.add_argument("--bc-batch", type=int, default=256, help="(legacy inline BC only)")
    p.add_argument("--bc-lr", type=float, default=3e-4, help="(legacy inline BC only)")
    p.add_argument("--learning-rate", type=float, default=3e-4)
    p.add_argument("--n-steps", type=int, default=2048)
    p.add_argument("--batch-size", type=int, default=64)
    p.add_argument("--n-epochs", type=int, default=10)
    p.add_argument("--gamma", type=float, default=0.99)
    p.add_argument("--clip-range", type=float, default=0.2)
    p.add_argument("--ent-coef", type=float, default=0.01)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--output", default=str(HERE / "models" / "opti_twin_ppo.zip"))
    args = p.parse_args()

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    torch.manual_seed(args.seed)
    np.random.seed(args.seed)

    print(f"[opti-twin] training PPO  seed={args.seed}  out={out_path}")

    # Step 1: BC warm start -- prefer pre-trained checkpoint, fall back to inline.
    bc_net: BCNet
    if args.legacy_inline_bc:
        print(f"[step 1/3] collecting {args.bc_pairs} scripted rollouts (legacy inline BC)")
        bc_obs, bc_acts = collect_bc_dataset(args.bc_pairs, seed=args.seed)
        for i, lab in enumerate(ACTIONS):
            n = int((bc_acts == i).sum())
            print(f"           {lab:<22} {n:6d}  ({n/len(bc_acts)*100:.1f}%)")
        bc_net = train_bc_inline(
            bc_obs, bc_acts,
            epochs=args.bc_epochs, batch_size=args.bc_batch, lr=args.bc_lr,
        )
    else:
        bc_path = Path(args.bc_init)
        if not bc_path.exists():
            raise SystemExit(
                f"[opti-twin] BC checkpoint not found at {bc_path}. "
                f"Run train_bc.py first or pass --legacy-inline-bc."
            )
        print(f"[step 1/3] loading BC checkpoint from {bc_path}")
        bc_net = load_bc_net(bc_path, obs_dim=OBS_DIM, n_actions=len(ACTIONS))

    # Optional M2/M3 hooks
    forecaster = None
    anomaly_detector = None
    if args.forecaster:
        from forecaster.lstm_forecaster import load_forecaster
        forecaster = load_forecaster(args.forecaster)
        print(f"[opti-twin] M2 forecaster loaded from {args.forecaster}")
    if args.anomaly:
        from anomaly.autoencoder import load_anomaly_detector
        anomaly_detector = load_anomaly_detector(args.anomaly)
        print(f"[opti-twin] M3 anomaly detector loaded from {args.anomaly}")

    # Optional: Optuna hyperparam search before the final training pass.
    tuned_params: dict[str, float] = {}
    if args.tune:
        print(f"[opti-twin] launching Optuna TPE study  trials={args.tune_trials}  "
              f"budget={args.tune_budget} steps/trial")
        tuned_params = run_optuna_study(args, bc_net, forecaster, anomaly_detector)

    # Step 2: Initialise PPO and inject BC weights.
    print(f"[step 2/3] initialising PPO and copying BC weights...")
    env = _make_env(forecaster=forecaster, anomaly_detector=anomaly_detector)
    ppo = PPO(
        "MlpPolicy",
        env,
        learning_rate=tuned_params.get("learning_rate", args.learning_rate),
        n_steps=int(tuned_params.get("n_steps", args.n_steps)),
        batch_size=args.batch_size,
        n_epochs=args.n_epochs,
        gamma=tuned_params.get("gamma", args.gamma),
        ent_coef=tuned_params.get("ent_coef", args.ent_coef),
        clip_range=tuned_params.get("clip_range", args.clip_range),
        seed=args.seed,
        verbose=0,
    )
    init_ppo_from_bc(ppo, bc_net)

    # Step 3: PPO fine-tune.
    print(f"[step 3/3] fine-tuning PPO for {args.total_timesteps} timesteps...")
    ppo.learn(total_timesteps=args.total_timesteps, progress_bar=False)

    ppo.save(str(out_path))
    print(f"[done] saved PPO model to {out_path}")
    if tuned_params:
        meta_path = out_path.with_suffix(".tuned_params.json")
        import json
        meta_path.write_text(json.dumps(tuned_params, indent=2))
        print(f"[done] tuned params -> {meta_path}")


if __name__ == "__main__":
    main()
