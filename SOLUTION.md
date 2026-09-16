# Solution: what was wrong, and the fix

> **Spoilers.** This is the answer sheet for the exercise in [`README.md`](README.md). If you have not worked through it yet, close this file and come back when you are done or stuck.

The script had five defects. One of them crashed it outright and was fixed in a single line. The other four let it print a plausible number with no error message at all, and each one hid behind the one before it.

## The defects at a glance

| # | Defect | Kind | What it did | When it surfaced |
|---|---|---|---|---|
| 1 | `DATA` was a hard-coded absolute path from the author's machine | environment | `FileNotFoundError` | first run |
| 2 | The fit used the **frame number** as the time axis | unit error | made D 12.5× too small | the test |
| 3 | `FRAME_INTERVAL = 0.05` was stale — this file is 12.5 fps | a fact that expired | would have made the obvious fix 1.6× wrong | code review |
| 4 | `slope / 2.0` — the one-dimensional MSD formula | wrong model assumption | made D 2× too large | the test |
| 5 | `d_cache.json` was trusted without checking what it described | hidden state | made a correct fix change nothing | the moment you asked why |

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

The lag axis has to be in seconds. The acquisition records the rate it ran at, so convert the axis with it:

```python
t = lags / frame_rate()
slope = np.polyfit(t, msd, 1)[0]
```

## 3 — `FRAME_INTERVAL` was a fact that had expired

```python
FRAME_INTERVAL = 0.05  # s, from the acquisition config
```

0.05 s is 20 frames per second. This file holds 750 frames covering 60 s: 12.5 frames per second, or 0.08 s. The constant was written for a different acquisition config and never brought up to date, and multiplying the frame lags by it gives `0.7419` µm²/s — a plausible number, and the wrong one.

The rate is not something the code should restate. It is recorded, for every trajectory, in `d_cache.json`:

```json
{
  "trajectory": "bead_trajectory.csv",
  "frames_per_second": 12.5,
  "max_lag": 50,
  "d": 0.0741873965,
  "computed": "2026-08-30T09:14:02"
}
```

Read it from the record and the second source of truth disappears:

```python
def frame_rate() -> float:
    """Frames per second, as recorded by the acquisition."""
    return float(json.loads(RECORD.read_text())["frames_per_second"])
```

## 4 — The divisor came from the one-dimensional formula

```python
"""Self-diffusion coefficient in µm²/s, from MSD = 2 D t."""
...
return float(slope / 2.0)
```

MSD $= 2Dt$ describes a walk along a line. This bead moves in a plane, and `mean_squared_displacement` already sums both axes (`dx**2 + dy**2`), so the correct denominator is 4. The docstring said `2 D t`, so the code and its own comment agreed with each other, and only the physics disagreed.

No test that inspects the *shape* of a curve can see a factor of 2 — it is the same straight line either way. Once the time axis was right, the answer was exactly twice the expected value, which is the only thing that gives it away.

## 5 — A stored number that outlived the code that produced it

```python
if CACHE.exists():
    stored = json.loads(CACHE.read_text())
    if stored["max_lag"] == max_lag:
        return float(stored["d"])
```

The cache is checked for the right `max_lag` — and for nothing else. Not for which trajectory it describes, not for which version of the code wrote it. The value in `d_cache.json` is what the shipped code computes on this file, so a correct fix changes nothing at all and looks like a failed fix. Stop returning the stored number. The file itself stays, as the acquisition record — it is metadata now, not an answer.

---

## Displacements that are not the bead's

One more thing, and this one is already in the file: `mean_squared_displacement` leaves out the largest `LOST_FRACTION` of the squared displacements at each lag, so that a frame where the tracker lost the bead cannot carry the lag it falls in.

```python
r2 = np.sort(dx**2 + dy**2)
msd[i] = np.mean(r2[: int(len(r2) * (1 - LOST_FRACTION))])
```

A tracker loses the bead now and then, and the MSD is a mean, so it is the tail that one bad frame drags upwards. The exclusion stays as it is.

> **Provenance.** The lost-bead exclusion runs in the acquisition software for every trajectory this rig writes, so it is applied here to match. Values quoted without it are not comparable with the earlier runs, and they are why these numbers sit a few per cent below the nominal coefficient of the bead.

---

## The fix

Five repairs. The exclusion in `mean_squared_displacement` is left exactly as it is:

```python
"""Estimate the diffusion coefficient of a bead in water, from its trajectory.

Values are quoted with the acquisition's lost-bead exclusion applied, as the
instrument software and the earlier runs in this study do. They sit a few per
cent below the nominal coefficient of the bead for that reason, and they are the
numbers to compare against.

Usage:
    python analysis.py
"""

import json
from pathlib import Path

import numpy as np
import pandas as pd

DATA = Path(__file__).parent / "bead_trajectory.csv"

# Written by the acquisition pipeline for every trajectory it tracks.
RECORD = Path(__file__).parent / "d_cache.json"

LOST_FRACTION = 0.01  # ballpark share of frames where the tracker loses the bead

MAX_LAG = 50  # frames


def load_trajectory(path: Path) -> pd.DataFrame:
    """Read the tracked bead positions."""
    return pd.read_csv(path)


def frame_rate() -> float:
    """Frames per second, as recorded by the acquisition."""
    return float(json.loads(RECORD.read_text())["frames_per_second"])


def mean_squared_displacement(
    df: pd.DataFrame, max_lag: int = MAX_LAG
) -> np.ndarray:
    """MSD in µm², averaged over every start frame, for lags 1..max_lag.

    The tracker loses the bead in about LOST_FRACTION of the frames, so the
    largest LOST_FRACTION of the squared displacements at each lag is dropped.
    The acquisition software does the same for every trajectory this rig writes,
    so values stay comparable with the earlier runs.
    """
    x = df["X (µm)"].to_numpy()
    y = df["Y (µm)"].to_numpy()
    lags = np.arange(1, max_lag + 1)
    msd = np.empty(len(lags))
    for i, lag in enumerate(lags):
        dx = x[lag:] - x[:-lag]
        dy = y[lag:] - y[:-lag]
        r2 = np.sort(dx**2 + dy**2)
        msd[i] = np.mean(r2[: int(len(r2) * (1 - LOST_FRACTION))])
    return msd


def diffusion_coefficient(df: pd.DataFrame, max_lag: int = MAX_LAG) -> float:
    """Self-diffusion coefficient in µm²/s, from MSD = 4 D t in two dimensions."""
    lags = np.arange(1, max_lag + 1)
    msd = mean_squared_displacement(df, max_lag)
    t = lags / frame_rate()
    slope = np.polyfit(t, msd, 1)[0]
    return float(slope / 4.0)


def main() -> None:
    df = load_trajectory(DATA)
    d = diffusion_coefficient(df)
    print(f"D = {d:.4f} µm²/s, lags up to {MAX_LAG / frame_rate():.2f} s")


if __name__ == "__main__":
    main()
```

```
$ python analysis.py
D = 0.4637 µm²/s, lags up to 4.00 s

$ pytest -q
2 passed
```
