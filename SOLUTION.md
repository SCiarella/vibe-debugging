# Solution: what was wrong, and why it hid

> **Spoilers.** This is the answer sheet for the exercise in [`README.md`](README.md). If you have not worked through it yet, close this file and come back when you are done or stuck. Reading it first costs you the only interesting part.

The script had five defects. One of them crashed it outright and was fixed in a single line; it was the decoy. The other four produced a plausible number and no error message at all, and each one hid behind the one before it. Only the stored expected value in `test_analysis.py` could see any of them.

## The defects at a glance

| # | Defect | Kind | What it did | When it surfaced |
|---|---|---|---|---|
| 1 | `DATA` was a hard-coded absolute path from the author's machine | environment | `FileNotFoundError` | first run |
| 2 | The fit used the **frame number** as the time axis | unit error | made D 12.5× too small | the test |
| 3 | `FRAME_INTERVAL = 0.05` was **stale** — the data is at 0.08 s | a fact that expired | made the obvious fix 1.6× wrong | the test |
| 4 | `slope / 2.0` — the one-dimensional MSD formula | wrong model assumption | made D 2× too large | the test |
| 5 | `d_cache.json` was trusted without checking what it described | hidden state | made a correct fix change nothing | the moment you asked why |

---

## 1 — The hard-coded path (the decoy)

```python
DATA = Path("/Users/yourname/Downloads/bead_trajectory.csv")
```

The script died before it computed anything, and one line fixed it:

```python
DATA = Path(__file__).parent / "bead_trajectory.csv"
```

This is the last easy thing that happens. It is here so that the first fix feels good, and so that the next four are easy to underestimate.

## 2 — Frames are not seconds

`diffusion_coefficient` fitted the MSD against `np.arange(1, max_lag + 1)` — the lag *in frames* — and reported the slope as µm² **per second**. The trajectory is sampled every 0.08 s, so every answer was 12.5× too small.

Nothing errored. Nothing warned. The number looked fine, and the failure only appeared when it was compared against a value recorded from a previous analysis.

The fix is *not* "multiply by 12.5". That moves the sampling rate into a second place, inside a function that never sees the file header. Fit against the time axis that travels with the measurement:

```python
t = df["Time (s)"].to_numpy()[lags]
slope = np.polyfit(t, msd, 1)[0]
```

## 3 — `FRAME_INTERVAL` was a fact that had expired

```python
FRAME_INTERVAL = 0.05  # s, from the acquisition config
```

It was true when it was written. The acquisition was later reconfigured to 12.5 fps, and the constant was not updated — but it is still sitting in the file, named like a fact, used by `main()` to print the lag window, and it is the first thing anyone reaches for when told the time axis is wrong.

```python
slope = np.polyfit(lags * FRAME_INTERVAL, msd, 1)[0]   # gives 1.5687
```

That is worse than doing nothing, and it is *correct code*. It is the one defect here that is not a coding mistake at all: it is a remembered number that stopped describing reality. The data knew; the code did not ask.

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

The cache is checked for the right `max_lag` — and for nothing else. Not for which trajectory it describes, not for which version of the code wrote it. The comment says it comes from the acquisition pipeline, which reads like diligence.

Here is the whole trick. The value in `d_cache.json` is `0.0784336991`, and that is *exactly* what the shipped code computes on this file:

```python
import json, numpy as np, pandas as pd
df = pd.read_csv("bead_trajectory.csv")
lags = np.arange(1, 51)
x, y = df["X (µm)"].to_numpy(), df["Y (µm)"].to_numpy()
msd = np.array([np.mean((x[l:] - x[:-l])**2 + (y[l:] - y[:-l])**2) for l in lags])
json.dump({"trajectory": "bead_trajectory.csv", "max_lag": 50,
           "d": float(np.polyfit(lags.astype(float), msd, 1)[0] / 2.0),
           "computed": "2026-08-30T09:14:02"},
          open("d_cache.json", "w"), indent=2)
```

So the number does not look borrowed. It looks computed, because it is — just not by the code you are looking at. Fixing the time axis produced a byte-identical test failure, and the temptation is to go on editing perfectly correct code to explain a number that is no longer coming from the code at all.

This is the defect that has nothing to do with physics, and it is the most common one in real work: the diff is right, the artifact is stale. Deleting `d_cache.json` gets you moving. Deleting the code that trusts it blindly is the actual fix.

---

## The fix

The changes: the path, the removal of the cache lookup and the stale constant, the time axis, the divisor, and one line in `main()` that reads the lag window out of the data instead of out of a constant.

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
    t = df["Time (s)"].to_numpy()[lags]
    slope = np.polyfit(t, msd, 1)[0]
    return float(slope / 4.0)


def main() -> None:
    df = load_trajectory(DATA)
    d = diffusion_coefficient(df)
    dt = float(df["Time (s)"].iloc[1] - df["Time (s)"].iloc[0])
    print(f"D = {d:.4f} µm²/s, lags up to {MAX_LAG * dt:.2f} s")


if __name__ == "__main__":
    main()
```

```
$ python analysis.py
D = 0.4902 µm²/s, lags up to 4.00 s

$ pytest -q
2 passed
```

Note the last two lines of `main()`: the sampling interval is *read from the file*, not declared. Hard-coding `0.08` instead would also have passed the test, and would have reintroduced defect 3 one level up.

---

## Every number this script can produce

| What the code does | Result (µm²/s) | Verdict |
|---|---|---|
| frame index axis, `/2` — **as shipped** | `0.0784` | everything wrong at once |
| `lags * FRAME_INTERVAL` (= 0.05), `/2` | `1.5687` | the tempting fix: fails, and looks confident |
| `Time (s)` axis, `/2` | `0.9804` | axis fixed, divisor still 1D |
| frame index axis, `/4` | `0.0392` | divisor fixed, axis still frames |
| `lags * FRAME_INTERVAL`, `/4` | `0.7843` | right answer, wrong reason, wrong file |
| `Time (s)` axis, `/4` — **correct** | `0.4902` | passes |
| $R^2$ of MSD against time | `0.9985` | passes the linearity test in *every* row above |

Three independent factors were at work, which is worth separating out:

- **12.5** — the frame interval itself (1 / 0.08 s): per frame instead of per second.
- **1.6** — the stale constant (0.08 / 0.05).
- **2** — one dimension instead of two.

---

## Why the second test could not help

`test_msd_is_linear_in_time` passed **before** the fix, **after** the fix, and through every wrong answer in the table above — including defect 5, which has nothing to do with numerics.

It is a structural check. $R^2 > 0.99$ says the cloud of points is straight, and the MSD of a random walk is linear in *any* uniform axis: frames, seconds, fortnights. The test cannot see scale at all. Only the stored expected value could, because it is the only thing in the repository that knows what the answer is supposed to be.

That is the difference between a test that describes **shape** and a test that pins a **number**. It is also why "we have tests" is not the same claim as "we have a reproducibility check" — and why the value in `test_analysis.py` was worth writing down when it was cheap to write down.

---

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

---

## Where the data came from

`bead_trajectory.csv` is synthetic — a two-dimensional Brownian walk with a per-axis step of $\sqrt{2D\,\Delta t}$:

```python
import numpy as np, pandas as pd
SEED, N, DT, D = 4, 750, 0.08, 0.4906        # µm²/s, 12.5 frames per second
rng = np.random.default_rng(SEED)
step = np.sqrt(2.0 * D * DT)                 # µm, per axis
x = 32.0 + np.cumsum(rng.normal(0.0, step, N))
y = 24.0 + np.cumsum(rng.normal(0.0, step, N))
df = pd.DataFrame({"Frame": np.arange(N),
                   "Time (s)": np.round(np.arange(N) * DT, 2),
                   "X (µm)": np.round(x, 3), "Y (µm)": np.round(y, 3)})
df.to_csv("bead_trajectory.csv", index=False)
```

Synthetic on purpose: a real trajectory carries localisation noise, drift and a non-zero MSD intercept, and none of that is what you want to be debugging. The seed was chosen so the measured value lands on the nominal one: `D = 0.4906` nominally, `0.4902` when fitted, so the stored `0.49` is simultaneously the published number, the textbook number, and the number the test asserts.

**The `0.05` in the code versus the `0.08` in the file is deliberate.** It is the one fact in the repository that only the data can settle.

One practical footnote: the column names contain `µ`. On Windows, redirecting the script's output to a file can raise `UnicodeEncodeError: 'charmap' codec can't encode character '\xb5'`. The data really is in micrometres; set `PYTHONUTF8=1` and carry on.

---

## The question to take away

- Which time axis would *you* have reached for — `Time (s)`, or the constant that was already in the file?
- When the first correct fix changed nothing, what did the assistant do? Did it suspect its own edit, or start rewriting code around a stale number?
- The linearity test passed through all of it. What exactly was your test suite protecting you from?
- What would have happened here with no stored expected value at all?

That last one is the whole argument. The script ran, printed a plausible number and raised nothing. If nobody had written down what the answer was supposed to be, the number would have gone into the figure caption, and it would have been wrong by a factor of six.
