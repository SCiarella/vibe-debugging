# Facilitator guide

## The two defects

`analysis.py` has one loud defect and one quiet one. The loud one is a decoy.

**Loud (decoy) — hard-coded path.** `DATA` points at
`/Users/yourname/Downloads/bead_trajectory.csv`, so the script dies with
`FileNotFoundError`. An assistant fixes this in one line, and it is tempting to
declare victory there. That is the teaching moment: the obvious problem is not
the interesting one.

**Quiet (the real bug) — the time axis is wrong.** The fit uses the frame
number as the x-axis. Frames are 0.05 s apart, so the slope comes out in µm²
**per frame** rather than µm² **per second** — exactly 20× too small:

| | value |
|---|---|
| script reports | `0.0245` µm²/s |
| correct answer | `0.4905` µm²/s |
| test asserts | `0.49 ± 0.05` |

The output looks completely plausible. Nothing errors. Nothing warns. Only the
test with the stored expected value catches it — which is the whole argument of
the workshop, made concrete in fifteen minutes.

## The fix

```python
def diffusion_coefficient(df: pd.DataFrame, max_lag: int = MAX_LAG) -> float:
    """Self-diffusion coefficient, from MSD = 4 D t in two dimensions."""
    lags = np.arange(1, max_lag + 1)
    msd = mean_squared_displacement(df, max_lag)
    t = df["Time (s)"].to_numpy()[lags]      # was: lags.astype(float)
    slope = np.polyfit(t, msd, 1)[0]
    return float(slope / 4.0)
```

Also change `DATA` to `Path(__file__).parent / "bead_trajectory.csv"`.

Verify: `python analysis.py` prints `D = 0.4905 µm²/s`, and `pytest -q` passes.

## Teaching sequence (15 minutes)

| Min | What you do |
|---|---|
| 0–2 | Everyone runs `python analysis.py`. It crashes. Ask them to read the error out loud. |
| 2–5 | **Before any assistant.** `df.head()` / `df.describe()`, and ask: *the script claims µm²/s — is the x-axis in seconds?* Let them find it or fail to. |
| 5–7 | Everyone runs `pytest -q`. The test fails with `0.0245` against `0.49`. This is the payoff: the number was plausible, the test was not. |
| 7–13 | Now the assistant. Give them the prompt below. Require: explain first, then edit, then show the diff. |
| 13–15 | Re-run the test, then **break it on purpose** (fit against `Frame` again) and watch it fail again. |

## The prompt to put on screen

```
Fix analysis.py so that it reports the diffusion coefficient in µm²/s,
using the Time (s) column as the time axis.

Context: bead_trajectory.csv has columns Frame, Time (s), X (µm), Y (µm).
Frames are 0.05 s apart; Time (s) is the same information in seconds.

Constraints: keep the function signatures, keep it readable, and explain
what was wrong. Do not change test_analysis.py.
```

## Debrief questions

- Did the assistant fix the path immediately and stop there?
- Did it tell you about the time axis before you asked?
- Did anyone get a fix that multiplies the frame slope by 20? That is the right
  number for the wrong reason — ask what happens when someone drops a frame or
  re-exports at another frame rate.
- Did anyone get a fix that divides by 2 instead of 4? That is the
  one-dimensional formula, MSD = 2 D t. The bead moves in the *plane*, so it is
  4 D t. Nobody is warned about this one.
- Did anyone's fix quietly produce µm² per frame and still get printed as
  µm²/s? The units label was a lie the whole time.
- What would have happened if you had no test?

That last question is the one to end on.

## The two tests, and why one of them is useless

`test_msd_is_linear_in_time` passes **before and after** the fix. It is a
structural check: the MSD of a random walk is linear in *any* uniform axis, so
the test cannot see the units at all. Point at this during the debrief — it is
the difference between a test that describes shape and a test that pins a
number, and it is why "we have tests" is not the same claim as "we have a
reproducibility check". Only the stored expected value could catch this bug.

## Running the LLM: your options, honestly

You said you want to run the model on your laptop. Four ways to do it, from
most to least reliable:

1. **Everyone uses the assistant they already have** (Copilot, Codeium, an
   institutional tool). Most reliable, zero setup, no bandwidth. If the room is
   larger than about eight people, do this.
2. **You drive, the room watches** (projector). Your local model, your laptop,
   no network. Perfectly safe and it still teaches everything — you narrate
   what the model gets wrong. Build in the mistake deliberately.
3. **You serve your local model on the room's network.** With Ollama:
   `OLLAMA_HOST=0.0.0.0:11434 ollama serve`, then participants point a client
   at `http://<your-laptop-ip>:11434`. Caveats worth knowing before you try:
   every participant's request competes for your one GPU, so twenty people will
   feel slow; your laptop must not sleep; participants' prompts and code pass
   through your machine, which is a data-protection question you should be able
   to answer; and many venue networks isolate clients from each other (AP
   isolation), in which case it simply will not connect.
4. **Each participant runs their own local model.** Most independence, most
   setup. `ollama pull qwen2.5-coder:1.5b` is about 1 GB and runs on almost
   anything; a 7B model is about 4.5 GB and wants ~8 GB of RAM. **They must
   download it before the session** — twenty people pulling 4 GB over
   conference WiFi is the single most likely way to lose fifteen minutes.

Whichever you choose, make it work **without a plugin**. The exercise only needs
a chat box: paste the script, paste the prompt. That removes the largest
failure mode (editor extensions and authentication) from a fifteen-minute block.

## Fallbacks

- **Model is slow.** Have the room write the prompt and predict the answer
  while it generates. Predicting is as instructive as receiving.
- **No model at all.** Hand out `SOLUTION.md` and run the debrief from it. The
  test still fails, so the diagnosis half still works.
- **Someone finishes early.** Ask them to run the Stokes–Einstein check in
  `SOLUTION.md` and recover the bead radius from the fitted `D`; it prints
  `1.001` µm, so the measurement agrees with the bead they were told they had.
  Then ask them to plot MSD against lag on log–log axes and confirm the slope
  is 1 (normal diffusion) rather than 0.8 (anomalous).
- **Someone's environment is broken.** Pair them with a neighbour. Do not debug
  one laptop in front of twenty people.

## Two things that will go wrong

- **`UnicodeEncodeError: 'charmap' codec can't encode character '\xb5'`** on
  Windows, but only when output is redirected to a file rather than printed to
  a terminal. The data really is in micrometres. Set `PYTHONUTF8=1` and move
  on.
- **A fix that hard-codes the frame interval**, e.g. `lags * 0.05`. It is
  correct, so do not call it wrong — but the sampling rate is now written in
  two places, and the second one is inside a function that never sees the file
  header. Ask what happens when someone re-exports at 100 fps. That is the
  same class of defect as the original bug, one level up.

## Where `bead_trajectory.csv` comes from

It is synthetic, and deliberately so: a real trajectory carries localisation
noise, drift and a non-zero MSD intercept, and none of that is what you want
the room debugging today. The recipe is ten lines:

```python
import numpy as np, pandas as pd
SEED, N, DT, D = 1322, 1200, 0.05, 0.4906        # µm²/s
rng = np.random.default_rng(SEED)
step = np.sqrt(2.0 * D * DT)                      # µm, per axis
x = 32.0 + np.cumsum(rng.normal(0.0, step, N))
y = 24.0 + np.cumsum(rng.normal(0.0, step, N))
df = pd.DataFrame({"Frame": np.arange(N),
                   "Time (s)": np.round(np.arange(N) * DT, 2),
                   "X (µm)": np.round(x, 3), "Y (µm)": np.round(y, 3)})
df.to_csv("bead_trajectory.csv", index=False)
```

`D = 0.4906` µm²/s is Stokes–Einstein for a 1 µm sphere in water at 25 °C
($D = k_BT/6\pi\eta a$, $\eta = 0.89$ mPa·s). The seed was chosen so that the
*measured* value lands on the nominal one — the fitted `D` is `0.4905` — so the
stored expected value of `0.49` is simultaneously the published number, the
textbook number and the number the test asserts. No coincidence has to be
explained away in front of the room.

Every number the room can produce:

| Fit | µm²/s | |
|---|---|---|
| against `Frame` (the bug as shipped) | `0.0245` | 20× too small |
| against `Time (s)` (correct) | `0.4905` | passes the test |
| against `Time (s)`, then `slope / 2` | `0.9810` | 1D formula, 2× too large |
| $R^2$ of MSD against time | `0.997` | passes the linearity test either way |

If you need a different trajectory, regenerate with the recipe above and re-derive
the stored value — do not hand-edit the CSV.
