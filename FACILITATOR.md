# Facilitator guide and reference solution

One file, everything: the defects, the fix, every number the room can produce,
the run sheet, the prompts, the debrief, and the recipe for the data.

**The exercise in one paragraph.** `analysis.py` claims to report a bead's
diffusion coefficient in µm²/s. It has five defects. One crashes it outright and
is fixed in a line, which is the decoy: the interesting ones let it print a
plausible number that is wrong, and each hides behind the one before it. Only
the stored expected value in `test_analysis.py` can see any of them. A
structural test cannot.

---

## 1. The defects

| # | Defect | Kind | Symptom | Surfaces when |
|---|---|---|---|---|
| 1 | `DATA` is a hard-coded absolute path from someone else's machine | environment / portability | `FileNotFoundError` | first run |
| 2 | The fit uses the **frame number** as the time axis | unit error | D is 12.5× too small | the test |
| 3 | `FRAME_INTERVAL = 0.05` is **stale**; the data is at 0.08 s | metadata drift | the tempting fix is 1.6× wrong | the test, only if the fix uses it |
| 4 | `slope / 2.0` — the one-dimensional MSD formula | wrong model assumption | D is 2× too large | the test, after 2 and 5 are fixed |
| 5 | `d_cache.json` is trusted without checking what it describes | hidden state / stale artifact | the number does not move when the code does | the room asks why its edit did nothing |

### 1 — Loud (the decoy): the hard-coded path

`DATA` points at `/Users/yourname/Downloads/bead_trajectory.csv`, so the script
dies with `FileNotFoundError`. An assistant fixes this in one line, and it is
tempting to declare victory there. That is the teaching moment: the obvious
problem is not the interesting one.

### 2 — Quiet: frames are not seconds

`diffusion_coefficient` fits the MSD against `np.arange(1, max_lag + 1)` — the
lag *in frames*. The slope therefore comes out in µm² **per frame** and is
reported as µm² **per second**. The data is sampled every 0.08 s, so the answer
is 12.5× too small. Nothing errors. Nothing warns.

The fix is not "multiply by 12.5": that moves the sampling rate into a second
place, inside a function that never sees the file. Fix it by fitting against the
time axis that ships with the measurement, `Time (s)`.

### 3 — The stale fact: `FRAME_INTERVAL`

`analysis.py` carries `FRAME_INTERVAL = 0.05  # s, from the acquisition config`,
and `main()` uses it to print the lag window. It was true when it was written;
the acquisition was later reconfigured to 12.5 fps and the constant was not
updated. It is the natural thing for an assistant to reach for — it is *in the
file it was given*, it is named like a fact, and the prompt names it too — and
it produces **1.5687**, which is worse than doing nothing.

This is the defect to watch in the room, because it is not a coding mistake. It
is a fact that used to be true. Code outlives the thing it was written about.

### 4 — Quiet: the divisor comes from the one-dimensional formula

`slope / 2.0` comes from MSD $= 2Dt$, which describes a walk along a line. The
trajectory is a walk in a plane, and `mean_squared_displacement` already sums
both axes (`dx**2 + dy**2`), so the correct denominator is 4. The docstring said
`MSD = 2 D t`, so the code and its comment agreed with each other and only the
physics disagreed. No test that inspects *shape* can see a factor of 2 — it is
the same straight line.

### 5 — Quiet: a stored value that outlives its code

`diffusion_coefficient` returns the number in `d_cache.json` if the file exists
and the `max_lag` matches — without checking that the stored value describes
this trajectory, or this version of the code. The cache holds `0.0784336991`,
which is exactly what the shipped code computes. That is why it is invisible:
the number does not look borrowed, it looks *computed*.

The sequence it produces is the most valuable 90 seconds of the session:

1. The room fixes the time axis.
2. The output does not change. Neither does the test failure: the assertion
   still reads `0.0784336991`, from the file, with the new code sitting right
   there.
3. Something else is supplying the answer. `ls` or `git status` finds it.

This is the modern failure mode. The diff is correct, the artifact is stale, and
the assistant will happily go on rewriting correct code to explain a number that
is no longer coming from the code.

---

## 2. The reference solution

The substantive changes: the path, the deletion of the cache and the stale
constant, the time axis, the divisor, and one line in `main()` that derives the
lag window from the data instead of from a constant.

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

Then delete `d_cache.json` — or, better, let the room decide whether deleting
the file is enough or whether the code that trusts it should go too. Both
answers are defensible and the question is worth asking out loud.

Verified output:

```
$ python analysis.py
D = 0.4902 µm²/s, lags up to 4.00 s

$ pytest -q
2 passed
```

`0.4902` is not merely "the number the test wanted": it is Stokes–Einstein for a
1 µm sphere in water at 25 °C. The exercise ends on a physical result, not an
arbitrary constant.

---

## 3. Every number the room can produce

| What the code does | Result (µm²/s) | Verdict |
|---|---|---|
| frame index axis, `/2` — **as shipped** | `0.0784` | everything wrong at once |
| `lags * FRAME_INTERVAL` (= 0.05), `/2` — the tempting fix | `1.5687` | fails, and looks confident |
| `Time (s)` axis, `/2` | `0.9804` | axis fixed, divisor still 1D |
| frame index axis, `/4` | `0.0392` | divisor fixed, axis still frames |
| `lags * FRAME_INTERVAL`, `/4` | `0.7843` | the fragile fix: right for the wrong file |
| `Time (s)` axis, `/4` — **correct** | `0.4902` | passes |
| $R^2$ of MSD against time | `0.9985` | passes the linearity test in *every* row above |

The three factors, for the debrief, all independent of each other:

- **12.5** — the frame interval itself (1 / 0.08 s): per frame instead of per
  second.
- **1.6** — the stale constant (0.08 / 0.05).
- **2** — one dimension instead of two.

The value in `d_cache.json` is `0.0784336991`, which is exactly what the shipped
code computes. That is not a coincidence and it is not meant to be spotted by
comparing numbers; it is meant to be spotted by noticing that the number stopped
responding to the code. If someone asks where the cache came from, the honest
in-story answer is "an earlier run of the pipeline, before the code was last
changed" — it is deliberately indistinguishable from a fresh computation, which
is the whole defect.

---

## 4. Run sheet (20 minutes)

| Min | What you do |
|---|---|
| 0–2 | Everyone runs `python analysis.py`. It crashes. Ask them to read the error out loud, then to fix it. That is defect 1, and it is the last easy thing that happens. |
| 2–5 | **Before any assistant.** `df.head()`, `df.describe()`, `df["Time (s)"].diff().unique()`. Ask the two questions: *the script claims µm²/s — is the x-axis in seconds?* and *which sampling interval is the data's opinion, and which is `FRAME_INTERVAL`'s?* Let them find it or fail to. |
| 5–7 | Everyone runs `pytest -q`. One test fails and one passes. Point at the passing one now: it will pass for the rest of the session, through every wrong answer in section 3. |
| 7–14 | Now the assistant, with the prompt in section 5. Require: explain first, then edit, then show the diff. |
| 9–11 | **The cache.** When the first fix does not move the number, do not rescue them immediately. Let the room sit with a correct diff and an unchanged answer for a minute: that discomfort is the lesson. Then ask what else could be supplying the value. |
| 14–17 | The stale constant, if the assistant used `FRAME_INTERVAL`: ask where that number came from and whether it describes this file. |
| 17–19 | The divisor: the answer is now exactly 2× too large. Ask why the test could not see it. |
| 19–20 | Re-run the test, then **break it on purpose** (fit against `Frame` again, deleting the cache first) and watch it fail again. |

**The 15-minute cut.** Delete `d_cache.json` before the room starts, and drop
defect 5; take the prompt's `lags * FRAME_INTERVAL` trap as the extra beat
instead. You lose the hidden-state lesson, which is the most modern one in the
set — but if you have 15 minutes and must choose, it is still the one to cut,
because everything else fits without it.

---

## 5. The prompt

```
analysis.py reports a diffusion coefficient that the value recorded in
test_analysis.py says is wrong. Work out why, explain it, then fix it.

Context: bead_trajectory.csv has columns Frame, Time (s), X (µm), Y (µm).
analysis.py keeps the sampling interval in FRAME_INTERVAL.

Constraints: keep the function signatures, keep it readable, and explain
what is wrong before you edit anything. Do not change test_analysis.py.
```

The context line names `FRAME_INTERVAL` without asserting its value. That is the
experiment: the constant is stale, the data is not, and the prompt does not say
which to believe. The assistant has to open the CSV to find out.

### The control experiment (optional, 2 min, worth it)

Run it a second time with the *human* supplying the stale number, which is what
actually happens in real work:

```
Context: bead_trajectory.csv has columns Frame, Time (s), X (µm), Y (µm).
Frames are 0.05 s apart.
```

An assistant that trusts the sentence writes `lags * 0.05`, gets `0.7843`, and
the test fails. Nothing about that is the assistant's fault: the human asserted
a fact and the assistant believed it. The pair of runs is the clearest possible
statement of the workshop's thesis — the model is not the oracle, the stored
value is. Remove `d_cache.json` between the two runs.

---

## 6. Debrief questions

- Did the assistant fix the path and stop there? How long did it take to say
  anything about the time axis?
- Which time axis did it choose — `Time (s)`, or the constant that was already
  in the file? If it chose the constant, would your code review have caught it?
- When the first fix changed nothing, what did the assistant do next? Did it
  suspect its own edit, or go looking for another explanation? Rewriting correct
  code to explain a stale number is the failure mode to name.
- Did anyone's fix divide by 2 instead of 4? That is the one-dimensional
  formula. The bead moves in a plane, so MSD $= 4Dt$. Nobody is warned about
  this one, and the MSD curve looks perfect either way.
- The linearity test passed through every wrong answer in section 3. If "we have
  tests" was your reproducibility argument, what exactly did it establish?
- What would have happened if you had no stored expected value — if the only
  test you had was the one that says the curve is straight?

That last question is the one to end on.

---

## 7. Why the second test is useless on purpose

`test_msd_is_linear_in_time` passes **before and after** the fix, and through
every defect in this exercise, including the stale-value one that has nothing to
do with numerics. It is a structural check: the MSD of a random walk is linear
in *any* uniform axis, so the test cannot see scale at all. It is the difference
between a test that describes shape and a test that pins a number, and it is why
"we have tests" is not the same claim as "we have a reproducibility check". Only
the stored expected value could catch any of it.

Point at this during the debrief, not before: letting the room discover that a
green test suite was never the thing protecting them is worth more than being
told.

---

## 8. Running the model: your options, honestly

Four ways, from most to least reliable:

1. **Everyone uses the assistant they already have** (Copilot, Codeium, an
   institutional tool). Most reliable, zero setup, no bandwidth. If the room is
   larger than about eight people, do this.
2. **You drive, the room watches** (projector). Your local model, your laptop,
   no network, and you narrate what it gets wrong. Build the mistake in
   deliberately.
3. **You serve your local model on the room's network.** With Ollama:
   `OLLAMA_HOST=0.0.0.0:11434 ollama serve`, then participants point a client
   at `http://<your-laptop-ip>:11434`. Caveats: every participant's request
   competes for your one GPU, so twenty people will feel slow; your laptop must
   not sleep; participants' prompts and code pass through your machine, which is
   a data-protection question you should be able to answer; and many venue
   networks isolate clients from each other (AP isolation), so it may simply not
   connect.
4. **Each participant runs their own local model.** Most independence, most
   setup. `ollama pull qwen2.5-coder:1.5b` is about 1 GB and runs on almost
   anything; a 7B model is about 4.5 GB and wants ~8 GB of RAM. **They must
   download it before the session** — twenty people pulling 4 GB over conference
   WiFi is the single most likely way to lose the slot.

Whichever you choose, make it work **without a plugin**. The exercise needs a
chat box: paste the file, paste the prompt. That removes the largest failure
mode (editor extensions and authentication) from a twenty-minute block.

---

## 9. Resetting between runs

The session consumes `d_cache.json` — that is the point of defect 5 — so a
rehearsal or a second session starts without it. Restore it before each run:

```bash
git checkout d_cache.json      # if it is committed, which it should be
```

It is currently **untracked** in this working tree. Commit it before you
present: an untracked file shows up in `git status`, which hands the room defect
5 for free. If it is lost, recreate it with the shipped code:

```bash
python - <<'PY'
import json, numpy as np, pandas as pd
df = pd.read_csv("bead_trajectory.csv")
lags = np.arange(1, 51)
x, y = df["X (µm)"].to_numpy(), df["Y (µm)"].to_numpy()
msd = np.array([np.mean((x[l:] - x[:-l])**2 + (y[l:] - y[:-l])**2) for l in lags])
json.dump({"trajectory": "bead_trajectory.csv", "max_lag": 50,
           "d": float(np.polyfit(lags.astype(float), msd, 1)[0] / 2.0),
           "computed": "2026-08-30T09:14:02"},
          open("d_cache.json", "w"), indent=2)
PY
```

That snippet is the cache's provenance: it is the shipped code's own answer,
which is exactly why the room cannot tell it apart from a computation.

Also `git checkout analysis.py test_analysis.py bead_trajectory.csv` to undo the
room's edits between runs.

---

## 10. Fallbacks

- **Model is slow.** Have the room write the prompt and predict the answer while
  it generates. Predicting is as instructive as receiving.
- **No model at all.** Hand out section 2 and run the debrief from it. The tests
  still fail, so the diagnosis half still works — and sections 1 and 3 carry the
  whole argument without a single AI in the room.
- **Someone finishes early.** Ask them to run the Stokes–Einstein check in
  section 12 and recover the bead diameter from the fitted `D`; it prints
  `1.001` µm. Then ask them to plot MSD against lag on log–log axes and confirm
  the slope is 1 (normal diffusion) rather than 0.8 (anomalous).
- **Someone is stuck.** Do not debug one laptop in front of twenty people; pair
  them with a neighbour. If the room is stuck on defect 5, the 60-second hint is
  "the script reads one file that is not the data — does that file still
  describe this trajectory?"
- **Someone's environment is broken.** Same answer as above. Do not debug it
  live.

### Two things that will go wrong

- **`UnicodeEncodeError: 'charmap' codec can't encode character '\xb5'`** on
  Windows, but only when output is redirected to a file rather than printed to a
  terminal. The data really is in micrometres. Set `PYTHONUTF8=1` and move on.
- **A fix that hard-codes the interval**, e.g. `lags * 0.08`. It is correct, so
  do not call it wrong — but the sampling rate is now written in two places, and
  the second one is inside a function that never sees the file header. Ask what
  happens when someone re-exports at 100 fps, or drops a frame. That is the same
  class of defect as the original bug, one level up.

---

## 11. Where `bead_trajectory.csv` comes from

It is synthetic, and deliberately so: a real trajectory carries localisation
noise, drift and a non-zero MSD intercept, and none of that is what you want the
room debugging. Nine lines:

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

`D = 0.4906` µm²/s is Stokes–Einstein for a 1 µm sphere in water at 25 °C
($D = k_BT/6\pi\eta a$, $\eta = 0.89$ mPa·s). The seed was chosen so that the
*measured* value lands on the nominal one — the fitted `D` is `0.4902` and the
recovered diameter is `1.001` µm — so the stored expected value of `0.49` is
simultaneously the published number, the textbook number and the number the test
asserts. No coincidence has to be explained away in front of the room.

`DT = 0.08` while the code says `0.05` is the deliberate divergence: it is the
one fact in the repository that only the data can settle. Do not "fix" the CSV
to match the code.

If you need a different trajectory, regenerate with the recipe above and
re-derive the stored value and section 3. Do not hand-edit the CSV.

---

## 12. The physics payoff

Dividing the slope by 4 assumes two-dimensional diffusion. With
$D = 0.4902$ µm²/s and $\eta = 0.89$ mPa·s at 25 °C:

```python
kT = 1.380649e-23 * 298.15
eta = 0.89e-3
r = kT / (6 * np.pi * eta * D * 1e-12)
print(2 * r * 1e6)   # 1.001  -> the bead really was 1 um across
```

It prints `1.001`. The measurement and the geometry agree, which is the whole
point of a stored expected value: not that a number is remembered, but that the
number means something.
