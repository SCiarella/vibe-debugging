# Solution: what was wrong, and the fix

> **Spoilers.** This is the answer sheet for the exercise in [`README.md`](README.md). If you have not worked through it yet, close this file and come back when you are done or stuck.

The script had four defects. Three of them produced a plausible number and no error message at all, and each one hid behind the one before it. Only the stored expected value in `test_analysis.py` could see any of them.

## The defects at a glance

| # | Defect | Kind | What it did | When it surfaced |
|---|---|---|---|---|
| 1 | `DATA` was a hard-coded absolute path from the author's machine | environment | `FileNotFoundError` | first run |
| 2 | The fit used the **frame number** as the time axis | unit error | made D 12.5× too small | the test |
| 3 | `slope / 2.0` — the one-dimensional MSD formula | wrong model assumption | made D 2× too large | the test |
| 4 | `d_cache.json` was trusted without checking what it described | hidden state | made a correct fix change nothing | the moment you asked why |

---

## 1 — The hard-coded path

```python
DATA = Path("/Users/yourname/Downloads/bead_trajectory.csv")
```

The script died before it computed anything, and one line fixed it:

```python
DATA = Path(__file__).parent / "bead_trajectory.csv"
```

## 2 — Frames are not seconds

`diffusion_coefficient` fitted the MSD against `np.arange(1, max_lag + 1)`, which is a lag *in frames*, and then reported the slope as µm² **per second**. Every answer came out 12.5× too small, and nothing errored.

The lag axis has to be in seconds. The module already records the sampling interval in `FRAME_INTERVAL`, so convert the lag axis with it before fitting:

```python
t = lags * FRAME_INTERVAL
slope = np.polyfit(t, msd, 1)[0]
```

## 3 — The divisor came from the one-dimensional formula

```python
"""Self-diffusion coefficient in µm²/s, from MSD = 2 D t."""
...
return float(slope / 2.0)
```

MSD $= 2Dt$ describes a walk along a line. This bead moves in a plane, and `mean_squared_displacement` already sums both axes (`dx**2 + dy**2`), so the correct denominator is 4. The docstring said `2 D t`, so the code and its own comment agreed with each other, and only the physics disagreed.

No test that inspects the *shape* of a curve can see a factor of 2 — it is the same straight line either way.

## 4 — A stored number that outlived the code that produced it

```python
if CACHE.exists():
    stored = json.loads(CACHE.read_text())
    if stored["max_lag"] == max_lag:
        return float(stored["d"])
```

The cache is checked for the right `max_lag` — and for nothing else. Not for which trajectory it describes, not for which version of the code wrote it. The value in `d_cache.json` is what the shipped code computes on this file, so a correct fix changes nothing at all and looks like a failed fix. Delete the file, and delete the code that trusts it.

---

## The fix

```python
"""Estimate the diffusion coefficient of a bead in water, from its trajectory.

Usage:
    python analysis.py
"""

from pathlib import Path

import numpy as np
import pandas as pd

DATA = Path(__file__).parent / "bead_trajectory.csv"

FRAME_INTERVAL = 0.05  # s, from the acquisition config

MAX_LAG = 50  # frames


def load_trajectory(path: Path) -> pd.DataFrame:
    """Read the tracked bead positions."""
    return pd.read_csv(path)


def mean_squared_displacement(
    df: pd.DataFrame, max_lag: int = MAX_LAG
) -> np.ndarray:
    """MSD in µm², averaged over every start frame, for lags 1..max_lag."""
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
    """Self-diffusion coefficient in µm²/s, from MSD = 4 D t in two dimensions."""
    lags = np.arange(1, max_lag + 1)
    msd = mean_squared_displacement(df, max_lag)
    t = lags * FRAME_INTERVAL
    slope = np.polyfit(t, msd, 1)[0]
    return float(slope / 4.0)


def main() -> None:
    df = load_trajectory(DATA)
    d = diffusion_coefficient(df)
    print(f"D = {d:.4f} µm²/s")


if __name__ == "__main__":
    main()
```

```
$ python analysis.py
D = 0.4902 µm²/s

$ pytest -q
2 passed
```

## Why 0.49 µm²/s

It is not a magic constant. It is Stokes–Einstein for a 1 µm sphere in water at 25 °C:

$$D = \frac{k_B T}{6\pi\eta a}$$

With $\eta = 0.89$ mPa·s, the measured $D = 0.4902$ µm²/s gives back a diameter of `1.001` µm:

```python
kT = 1.380649e-23 * 298.15
eta = 0.89e-3
r = kT / (6 * np.pi * eta * 0.4902 * 1e-12)
print(2 * r * 1e6)   # 1.001
```

The measurement and the geometry agree. That is what a stored expected value is for: not that a number is remembered, but that the number means something.
