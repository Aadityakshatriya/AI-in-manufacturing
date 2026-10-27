"""CNN autoencoder: learns what healthy cutting sounds like.

Input: 0.16 s of vibration (4,096 samples at 25 kHz) from the five table-side sensors, as a
5-channel 1-D signal. The encoder is six convolution layers; each one slides 7-sample filters along
time and halves the length (4,096 → 64), while the number of filters grows (5 → 256). A final linear
layer squeezes everything into a 64-number fingerprint. The decoder is the mirror image and has to
rebuild the original 5 × 4,096 signal from those 64 numbers.

It is trained only on cycles from the early, healthy part of each training cutter's life. Afterwards:
  - the fingerprint summarises how a cut sounded;
  - the health score is how badly the decoder rebuilds the signal. A cutter that still sounds
    healthy is rebuilt well; as it wears, its sound drifts away from what the network learned and
    the error grows.
About 3.8 million learned numbers in total.
"""

import torch
from torch import nn

WIN = 4096
LATENT = 64
CHANNELS = (5, 32, 64, 128, 128, 256, 256)  # input sensors, then filters per layer


def down(cin: int, cout: int) -> nn.Sequential:
    return nn.Sequential(nn.Conv1d(cin, cout, 7, stride=2, padding=3), nn.BatchNorm1d(cout), nn.GELU())


def up(cin: int, cout: int, last: bool = False) -> nn.Module:
    conv = nn.ConvTranspose1d(cin, cout, 8, stride=2, padding=3)  # exactly doubles the length
    return conv if last else nn.Sequential(conv, nn.BatchNorm1d(cout), nn.GELU())


class CNNAutoencoder(nn.Module):
    def __init__(self, latent: int = LATENT):
        super().__init__()
        c = CHANNELS
        self.encoder = nn.Sequential(*[down(c[i], c[i + 1]) for i in range(len(c) - 1)])
        self.short = WIN // 2 ** (len(c) - 1)  # 64 time steps left after six halvings
        self.to_latent = nn.Linear(c[-1] * self.short, latent)
        self.from_latent = nn.Linear(latent, c[-1] * self.short)
        r = c[::-1]
        self.decoder = nn.Sequential(*[up(r[i], r[i + 1], last=(i == len(r) - 2)) for i in range(len(r) - 1)])

    def encode(self, x: torch.Tensor) -> torch.Tensor:
        """x [B, 5, 4096] → fingerprint [B, 64]."""
        return self.to_latent(self.encoder(x).flatten(1))

    def decode(self, z: torch.Tensor) -> torch.Tensor:
        h = self.from_latent(z).view(z.shape[0], CHANNELS[-1], self.short)
        return self.decoder(h)

    def forward(self, x: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        z = self.encode(x)
        return self.decode(z), z


def n_params(model: nn.Module) -> int:
    return sum(p.numel() for p in model.parameters())
