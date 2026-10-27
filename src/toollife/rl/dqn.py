"""Masked Double DQN, CleanRL style (rl-design.md §5.3).

In two sentences: a network scores every joint action, the agent picks the best allowed one (or a
random allowed one while exploring), and it learns from a replay buffer of past steps, using 3-step
returns and a slowly updated copy of itself for the targets. Stable-Baselines3's DQN cannot rule
out actions, so masks are applied here by hand, both when acting and inside the target's argmax.

Details: dueling head, Huber loss, Adam, soft target update (tau), epsilon falls linearly from 1 to
0.05 over the first 20 % of steps. The workshop never terminates (episodes are only cut off), so
every target bootstraps; at a cut-off the pending n-step returns bootstrap from the last observation.

Reward centering (Naik et al. 2024, "Reward centering", RLC): a running average of the reward is
subtracted from every reward before it is stored. In a task that never ends this shifts every action
value by the same constant, so the best action does not change, but the network no longer has to
learn a large constant (≈ average reward / (1 − gamma)) on top of the small keep-vs-change
differences; without it DQN stayed far from the DP in the single-machine check.
"""

from __future__ import annotations

from collections import deque

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F


class QNet(nn.Module):
    def __init__(self, n_obs: int, n_act: int, width: int = 256):
        super().__init__()
        self.body = nn.Sequential(nn.Linear(n_obs, width), nn.ReLU(), nn.Linear(width, width), nn.ReLU())
        self.value = nn.Linear(width, 1)
        self.adv = nn.Linear(width, n_act)

    def forward(self, x):
        z = self.body(x)
        a = self.adv(z)
        return self.value(z) + a - a.mean(dim=1, keepdim=True)


def masked_argmax(q: torch.Tensor, mask: torch.Tensor) -> torch.Tensor:
    return q.masked_fill(~mask, -torch.inf).argmax(dim=1)


class MaskedDQN:
    def __init__(self, envs, lr=1e-4, gamma=0.995, buffer_size=200_000, batch_size=256, learning_starts=10_000,
                 train_freq=4, tau=0.005, n_step=3, eps_end=0.05, eps_frac=0.2, width=256, seed=0,
                 center_rewards=True, center_rate=1e-3):
        self.envs, self.gamma, self.n_step = envs, gamma, n_step
        self.center_rewards, self.center_rate, self.r_bar = center_rewards, center_rate, 0.0
        self.batch_size, self.learning_starts, self.train_freq, self.tau = batch_size, learning_starts, train_freq, tau
        self.eps_end, self.eps_frac = eps_end, eps_frac
        self.rng = np.random.default_rng(seed)
        torch.manual_seed(seed)
        n_obs = envs[0].observation_space.shape[0]
        self.n_act = envs[0].action_space.n
        self.q = QNet(n_obs, self.n_act, width)
        self.q_target = QNet(n_obs, self.n_act, width)
        self.q_target.load_state_dict(self.q.state_dict())
        self.opt = torch.optim.Adam(self.q.parameters(), lr=lr)
        N = buffer_size
        self.buf = dict(obs=np.zeros((N, n_obs), np.float32), act=np.zeros(N, np.int64), ret=np.zeros(N, np.float32),
                        nxt=np.zeros((N, n_obs), np.float32), nmask=np.zeros((N, self.n_act), bool),
                        disc=np.zeros(N, np.float32))
        self.size = self.pos = 0
        self.seed = seed

    def _add(self, obs, act, ret, nxt, nmask, disc):
        b, i = self.buf, self.pos
        b["obs"][i], b["act"][i], b["ret"][i], b["nxt"][i], b["nmask"][i], b["disc"][i] = obs, act, ret, nxt, nmask, disc
        self.pos = (self.pos + 1) % len(b["act"])
        self.size = min(self.size + 1, len(b["act"]))

    def _flush(self, pending, nxt, nmask, all_of_them: bool, terminal: bool = False):
        """Turn pending (obs, act, reward) steps into n-step transitions ending at `nxt`
        (no bootstrap after a true end of episode)."""
        while pending and (all_of_them or len(pending) >= self.n_step):
            ret = sum(r * self.gamma ** k for k, (_, _, r) in enumerate(pending))
            o, a, _ = pending[0]
            self._add(o, a, ret, nxt, nmask, 0.0 if terminal else self.gamma ** len(pending))
            pending.popleft()
            if not all_of_them:
                break

    def predict(self, obs, mask) -> int:
        with torch.no_grad():
            q = self.q(torch.as_tensor(obs[None], dtype=torch.float32))
        return int(masked_argmax(q, torch.as_tensor(mask[None])).item())

    def _train_step(self):
        idx = self.rng.integers(0, self.size, self.batch_size)
        b = {k: torch.as_tensor(v[idx]) for k, v in self.buf.items()}
        with torch.no_grad():
            a_star = masked_argmax(self.q(b["nxt"]), b["nmask"])                     # online net picks
            q_next = self.q_target(b["nxt"]).gather(1, a_star[:, None]).squeeze(1)  # target net scores
            y = b["ret"] + b["disc"] * q_next
        q = self.q(b["obs"]).gather(1, b["act"][:, None]).squeeze(1)
        loss = F.smooth_l1_loss(q, y)
        self.opt.zero_grad()
        loss.backward()
        nn.utils.clip_grad_norm_(self.q.parameters(), 10.0)
        self.opt.step()
        with torch.no_grad():
            for p, pt in zip(self.q.parameters(), self.q_target.parameters()):
                pt.mul_(1 - self.tau).add_(self.tau * p)
        return float(loss.detach())

    def learn(self, total_steps: int, log_every: int = 50_000, log=print):
        envs = self.envs
        obs = [e.reset(seed=self.seed * 1000 + i)[0] for i, e in enumerate(envs)]
        masks = [e.action_masks() for e in envs]
        pending = [deque() for _ in envs]
        ep_ret = np.zeros(len(envs))
        recent = deque(maxlen=20)
        step, grad_debt = 0, 0.0
        while step < total_steps:
            eps = max(self.eps_end, 1 - (1 - self.eps_end) * step / (self.eps_frac * total_steps))
            with torch.no_grad():  # one forward pass for all envs
                q = self.q(torch.as_tensor(np.stack(obs), dtype=torch.float32))
                greedy = masked_argmax(q, torch.as_tensor(np.stack(masks))).numpy()
            for i, e in enumerate(envs):
                if self.rng.random() < eps:
                    a = int(self.rng.choice(np.flatnonzero(masks[i])))
                else:
                    a = int(greedy[i])
                nxt, r, term, trunc, _ = e.step(a)
                nmask = e.action_masks()
                ep_ret[i] += r
                if self.center_rewards:
                    self.r_bar += self.center_rate * (r - self.r_bar)
                    r = r - self.r_bar
                pending[i].append((obs[i], a, r))
                self._flush(pending[i], nxt, nmask if not term else np.ones_like(nmask),
                            all_of_them=term or trunc, terminal=term)
                if term or trunc:
                    recent.append(ep_ret[i])
                    ep_ret[i] = 0.0
                    nxt, _ = e.reset()
                    nmask = e.action_masks()
                obs[i], masks[i] = nxt, nmask
                step += 1
                if step % log_every == 0 and recent:
                    log(f"  dqn step {step:,}  eps {eps:.2f}  mean episode return {np.mean(recent):.1f}")
            if step >= self.learning_starts and self.size >= self.batch_size:
                grad_debt += len(envs) / self.train_freq
                while grad_debt >= 1:
                    self._train_step()
                    grad_debt -= 1
        return self

    def save(self, path):
        torch.save(self.q.state_dict(), path)
