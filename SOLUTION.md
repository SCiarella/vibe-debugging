# Reference solution

Facilitator copy. Hand this out only if the room cannot run an assistant.

## What was wrong

1. **`DATA` was a hard-coded absolute path** from someone else's machine. The
   script crashed instead of running. Loud, obvious, and a decoy.
2. **The mean squared displacement was fitted against the frame number, not
   against time.** Frames are 0.05 s apart, so the slope came out in µm² per
   *frame*. It read `0.0245` µm²/s instead of `0.4905` — a factor of exactly
   20. Nothing errored, and the number looked entirely plausible.

## The fixed script

```python
"""Estimate the diffusion coefficient of a bead in water, from its trajectory.

Usage:
    python analysis.py
"""

from pathlib import Path

import numpy as np
import pandas as pd

DATA = Path(__file__).parent / "bead_trajectory.csv"

MAX_LAG = 50  # frames


def load_trajectory(path: Path) -> pd.DataFrame:
    """Read the tracked bead positions."""
    return pd.read_csv(path)


def mean_squared_displacement(
    df: pd.DataFrame, max_lag: int = MAX_LAG
) -> np.ndarray:
    """MSD in um^2, averaged over every start frame, for lags 1..max_lag."""
    x = df["X (µm)"].to_numpy()
    y = df["Y (µm)"].to_numpy()
    lags = np.arange(1, max_lag + 1)
    msd = np.empty(len(lags))
    for i, lag in enumerate(lags):
        dx = x[lag:] - x[:-lag]
        dy = y[lag:] - y[:-lag]
        msd[i] = np.mean(dx**2 + dy**2)
    return msd


def diffusion_coefficient(df: pd.DataFrame, max_lag: int = MAX_LAG) -> float:
    """Self-diffusion coefficient, from MSD = 4 D t in two dimensions."""
    lags = np.arange(1, max_lag + 1)
    msd = mean_squared_displacement(df, max_lag)
    t = df["Time (s)"].to_numpy()[lags]
    slope = np.polyfit(t, msd, 1)[0]
    return float(slope / 4.0)


def main() -> None:
    df = load_trajectory(DATA)
    d = diffusion_coefficient(df)
    print(f"D = {d:.4f} µm²/s")


if __name__ == "__main__":
    main()
```

The only substantive change is the two lines inside `diffusion_coefficient`.

## Expected results after the fix

```
$ python analysis.py
D = 0.4905 µm²/s

$ pytest -q
2 passed
```

Note that `0.4905` is not merely "the number the test wanted": it is
Stokes–Einstein for a 1 µm sphere in water at 25 °C. The exercise ends on a
physical result, not an arbitrary constant.

## Every way the room can get a plausible number

| What the fix does | Result (µm²/s) | Verdict |
|---|---|---|
| `t = lags` — the bug as shipped | `0.0245` | 20× too small |
| `t = lags * 0.05` | `0.4905` | passes — but the frame interval is now hard-coded in a second place |
| `t = df["Time (s)"].to_numpy()[lags]` | `0.4905` | passes, and the sampling rate lives only in the data |
| `slope / 2` instead of `slope / 4` | `0.9810` | the one-dimensional formula — the bead moves in a plane, so MSD = 4 D t |

Swapping the division is the most instructive failure, because the assistant
will not flag it. It silently assumed one dimension, produced a number twice
the right size, and the MSD curve still looked perfect. It is the same class
of error as the original bug: a plausible answer that came from the wrong
axis.

The `lags * 0.05` variant is worth a two-minute detour if the room is fast.
Ask what happens the first time a frame is dropped, or the trajectory is
re-exported at 100 fps.

## The physics payoff

Dividing the slope by 4 assumes two-dimensional diffusion. With $D = 0.4905$
µm²/s and $\eta = 0.89$ mPa·s at 25 °C:

```python
kT = 1.380649e-23 * 298.15
eta = 0.89e-3
r = kT / (6 * np.pi * eta * D * 1e-12)
print(2 * r * 1e6)   # 1.001  -> the bead really was 1 um across
```

It prints `1.001`. The measurement and the geometry agree, which is the whole
point of a stored expected value: not that a number is remembered, but that
the number means something.
