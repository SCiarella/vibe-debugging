# Hands-on: fix a script that runs but lies

**Time:** about 15 minutes · **You need:** Python, and an AI coding assistant
(your own, or the one the facilitator is serving)

The script measures how fast a bead diffuses in water. It is the sort of
number you would put in a paper: a diffusion coefficient in µm²/s.

## What is in this folder

| File | What it is |
|---|---|
| `analysis.py` | A small script that reports the diffusion coefficient of a bead |
| `bead_trajectory.csv` | 1200 frames of one tracked bead — 60 s at 20 fps |
| `test_analysis.py` | A test with a stored expected value |

## Step 1 — Run it (1 min)

```bash
python analysis.py
```

It does not work. Read the error before you touch anything.

## Step 2 — Look at the data, not the code (3 min)

```bash
python -c "import pandas as pd; d = pd.read_csv('bead_trajectory.csv'); print(d.head()); print(d.describe())"
```

Two questions worth answering before you ask an assistant for anything:

1. What columns are actually in this file?
2. The script claims to report **µm²/s**. What is the x-axis it is fitting
   against — is it measured in seconds?

## Step 3 — Run the test (2 min)

```bash
pytest -q
```

The test fails. That failure is the most useful information you have.
What is the script reporting, and what should it be?

## Step 4 — Now use the assistant (5 min)

Use this three-part prompt (objective, context, constraints). It is short on
purpose — try writing your own version first if you prefer.

```
Fix analysis.py so that it reports the diffusion coefficient in µm²/s,
using the Time (s) column as the time axis.

Context: bead_trajectory.csv has columns Frame, Time (s), X (µm), Y (µm).
Frames are 0.05 s apart; Time (s) is the same information in seconds.

Constraints: keep the function signatures, keep it readable, and explain
what was wrong. Do not change test_analysis.py.
```

Then:

- Ask it to **explain the bug before it edits anything**. Did it find the real
  one, or only the obvious one?
- Watch what else it reaches for. If it proposes multiplying the frame slope by
  20, ask why that number: it is a copy of `1 / 0.05`, and it will be wrong the
  day someone re-exports the trajectory at another frame rate. If it divides by
  2 instead of 4, it has assumed one dimension instead of two.
- Read the diff. Every line.

## Step 5 — Verify (3 min)

```bash
pytest -q
```

Now break it on purpose: fit against `Frame` again and confirm the test fails.
**A test you have never seen fail is not a test.**

## Definition of done

- [ ] `python analysis.py` prints a diffusion coefficient of about 0.49 µm²/s
- [ ] `pytest -q` passes
- [ ] You can say out loud what the bug was and why the wrong answer looked
      plausible
- [ ] The prompt you used is saved next to the code (a comment, or a
      `PROMPTS.md`)

## Where the number comes from

0.49 µm²/s is not a magic constant. It is Stokes–Einstein,
$D = k_B T / 6\pi\eta a$, for a 1 µm sphere in water at 25 °C. If you have five
minutes spare, recover the bead radius from your fitted $D$ and check that it
is 0.5 µm.

## Data

`bead_trajectory.csv` is synthetic — a two-dimensional Brownian walk with a
per-axis step of $\sqrt{2D\,\Delta t}$, using $D = 0.4906$ µm²/s and
$\Delta t = 0.05$ s. Synthetic on purpose: a real trajectory would carry
localisation noise and drift, and you want to be debugging the units today,
not the physics.
