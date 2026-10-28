"""1-D CNN that reads raw vibration and says how much of the cutter's life is used.

Input: 5 table-side vibration sensors x any number of samples (trained on 0.14 s crops of the 0.16 s
windows, 4,096 samples at 25 kHz). The body is the autoencoder's encoder at half the width: six
convolution layers, each sliding 7-sample filters along time and halving the length, 5 -> 128 filters.
Each filter's average and peak over time go to one output squeezed between 0 (new) and 1 (failing).
About 0.22 million learned numbers, against 4.0 million in the autoencoder.
"""

import torch
from torch import nn

from toollife.models.autoencoder import down

CHANNELS = (5, 16, 32, 64, 64, 128, 128)  # input sensors, then filters per layer


class RawCNN(nn.Module):
    def __init__(self):
        super().__init__()
        c = CHANNELS
        self.encoder = nn.Sequential(*[down(c[i], c[i + 1]) for i in range(len(c) - 1)])
        self.head = nn.Sequential(nn.Dropout(0.2), nn.Linear(2 * c[-1], 1))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """x [B, 5, T] -> fraction of life used [B]."""
        h = self.encoder(x)
        h = torch.cat([h.mean(-1), h.amax(-1)], 1)  # average and peak of each filter: works for any T
        return torch.sigmoid(self.head(h)).squeeze(1)
