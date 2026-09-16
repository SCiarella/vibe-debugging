# Hands-on: fix a script that runs but lies

*The person who wrote `analysis.py` has left the lab. Before they went, they did the one thing that makes analysis code reproducible: they left `test_analysis.py` behind, pinning the diffusion coefficient to 0.49 µm²/s for a 1 µm bead in water at 25 °C. It is a property of the bead, so a new trajectory of that bead should reproduce it.*

*You have just added a new trajectory, and it looks a little different from the one the paper used. You want to confirm the code before the number goes into a figure caption. The test is the only witness you have.*

> **Your goal.** Get a consistent diffusion coefficient.
>
> - `python analysis.py` prints something close to **0.49 µm²/s**
> - `pytest -q` reports **2 passed**

**What you take away:**  
*Project structure:* why a project declares what it depends on in `pyproject.toml` rather than relying on whatever happens to be installed. 
*Tests:* what you get from writing the expected answer down before you need it. 
*Vibe coding:* debugging with an assistant, predict, change one thing, run the test, read the failure, keep the assistant honest about what it actually knows.

<details>
<summary><b>Where 0.49 µm²/s comes from, and where the trajectory comes from</b></summary>

0.49 µm²/s is not a magic constant. It is Stokes–Einstein, $D = k_B T / 6\pi\eta a$, for a 1 µm sphere in water at 25 °C. If you have five minutes spare, recover the bead radius from your fitted $D$ and check that it is 0.5 µm.

`bead_trajectory.csv` is synthetic — a two-dimensional Brownian walk with a per-axis step of $\sqrt{2D\,\Delta t}$, using $D = 0.4906$ µm²/s and $\Delta t = 0.08$ s, 12.5 frames per second, 750 frames of it.

Synthetic on purpose: a real trajectory would carry localisation noise and drift, and you want to be debugging the units today, not the physics.

`Time (s)` is not decoration. It is the only statement of the sampling interval that travels with the measurement — every other copy of that number lives in someone's code, and code outlives the thing it was written about.

</details>

## What is in this folder

| File | What it is |
|---|---|
| `analysis.py` | The script that reports the diffusion coefficient of a bead |
| `bead_trajectory.csv` | Your new trajectory — 750 frames, 60 s of wall clock |
| `test_analysis.py` | Two tests, one of which pins the expected value |
| `d_cache.json` | A diffusion coefficient stored by an earlier run of the pipeline |
| `pyproject.toml` | The dependencies, so one command installs them |
| `SOLUTION.md` | An answer sheet for this exercise |

> **The rules.** The test is the judge: it is the only thing in this folder that knows the answer, and the script's output is an opinion. **Do not edit `test_analysis.py`.**  Run the test after every change, especially when you are sure.

---

## Before you start 

Skip this if you already have a working Python and an editor you like.

- **Python 3.9 or newer** — <https://www.python.org/downloads/>. On Windows, tick *Add python.exe to PATH* in the installer, or none of the commands below will be found. Check with `python3 --version`.
- **VS Code** — <https://code.visualstudio.com/Download>, plus the [Python extension](https://marketplace.visualstudio.com/items?itemName=ms-python.python) so the editor can find the `.venv` you create next (*Python: Select Interpreter*).

> **Which assistant?** Use whatever you already have — Copilot, Codeium, an institutional tool, a browser tab — or the **GitHub Copilot free plan** in VS Code (sign in with a GitHub account; this exercise uses a handful of chat requests). 


## Step 0 — Install the dependencies

Create a virtual environment, then let `pip` read the dependency list out of `pyproject.toml`. From the folder that contains this README:

```bash
python3 -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -e ".[test]"
```

Check that it worked:

```bash
python -c "import numpy, pandas, pytest; print('ok')"
```

If it prints `ok`, the environment is active. If `numpy` is not found, it is not — check that `which python` points somewhere inside `.venv/`.

<details>
<summary><b>What all of that actually did</b></summary>

`python3 -m venv .venv` copies a Python interpreter and its package directory into `.venv/`. `source .venv/bin/activate` puts that copy first on your `PATH`, so from then on `python` and `pip` mean *this project's* Python and everything installs into `.venv/` rather than into your system Python. `.venv/` is already in `.gitignore`. `deactivate` leaves the environment, and deleting the folder throws it away — starting over is cheap, so do it whenever the environment looks wrong.

`-e` means *editable*: `analysis.py` is installed as a package that points back at this folder, so the code you edit is the code that runs, and you never reinstall after a change. The `[test]` extra adds `pytest`; if you only want to run the script, plain `pip install -e .` is enough.

</details>

---

## Step 1 — First (broken) run 

```bash
python analysis.py
```

It does not work. Read the error before you touch anything.

> **Checkpoint.** You have read the traceback and you have not touched the physics yet. Fix the crash, get the script running, and then answer one question before you go further: does a script that *runs* correctly produce a *correct* number?

## Step 2 — Look at the data 

```bash
python -c "import pandas as pd; d = pd.read_csv('bead_trajectory.csv'); print(d.head()); print(d.describe()); print(d['Time (s)'].diff().unique())"
```

Three questions worth answering before you open a chat box:

1. What columns are actually in this file?
2. The script claims to report **µm²/s**. Are the units correct?
3. The script keeps a sampling interval in `FRAME_INTERVAL`. Compare it with the spacing you just printed. Which of the two is the data's opinion, and which is somebody's memory?

> **Checkpoint.** Everything the assistant gets wrong in Step 4, it gets wrong because one of these three answers was assumed rather than checked. If you cannot answer all three, you are about to hand it a trap.

## Step 3 — Run the test

```bash
pytest -q
```

One test fails and one passes. The failure is the most useful information you have: it contains both the number the script is reporting and the number it should be reporting, and the gap between them is the size of the bug.

Look at the test that *passed*, too. It will pass for the rest of the session, whatever you do. Ask yourself what it is actually protecting you from.

## Step 4 — Bring in the assistant

**Ask mode first.** You can use this prompt example:
```
analysis.py reports a diffusion coefficient that the value recorded in test_analysis.py says is wrong. Work out why, explain it, then show me the fix.

Context: bead_trajectory.csv has columns Frame, Time (s), X (µm), Y (µm). analysis.py keeps the sampling interval in FRAME_INTERVAL.

Constraints: keep the function signatures, keep it readable. Do not change test_analysis.py.
```
or write your own. The assistant will read the whole folder, so it can see the data, the script, and the test. It cannot write to disk, so it will propose a diff rather than changing anything.

**Then agent mode.** Same task, but now it can edit `analysis.py` and run the tests itself. It will probably run `pytest` and keep going until the suite is green, so plan to spend your time on the result rather than on the conversation. *Read the diff anyway: **you** are the one whose name goes on the paper*.

| | Ask mode | Agent mode |
|---|---|---|
| What you get back | a proposed diff | a modified working tree |
| Does it run `pytest` | no | yes |

The difference between them is what they can *do*, not what they can *see*. Both read every file in the folder, and whatever is sitting there becomes part of the context before anyone has asked a question. The tests are what tell you whether that mattered.

> **Checkpoint.** The assistant is fast, tireless and never unsure, and none of that is evidence. The test is the only thing here that cannot be talked into a wrong answer.

## Step 5 — Verify, then break it on purpose

```bash
python analysis.py
pytest -q
```

The script should print `D = 0.4902 µm²/s`, and both tests should pass.

Now the interesting half: **you** introduce the fault, and the assistant has to find it without being told what you did. Pick one, or invent your own, and hand over nothing but the symptom:

| Break it like this | What you see | Does the suite notice? |
|---|---|---|
| `slope / 4.0` → `slope / 2.0` | `D = 0.9804` | yes |
| compute the MSD from the first pair only, `(x[lag] - x[0])**2 + (y[lag] - y[0])**2` | `D = 0.1570` | yes |
| `float(slope / 4.0)` → `int(slope / 4.0)` | `D = 0.0000` | yes |
| `{d:.4f}` → `{d * 1000:.4f}` in the print inside `main()` | `D = 490.2106` | **no** |

That last row is the one worth doing. The tests call `diffusion_coefficient` directly and never touch `main()`, so a fault there leaves the suite green: the run passes, and the number in the caption is wrong. It is the same shape of failure as the one you started with, and nobody's test suite is watching for it.

Watch what the assistant does with a green suite and no failure message to read. Does it reason about the code, or ask you what changed? Does it believe the tests, or the number it just printed? **A test you have never seen fail is not a test.**

---

## You are done when

- [ ] `python analysis.py` prints a diffusion coefficient of about 0.49 µm²/s
- [ ] `pytest -q` reports `2 passed`
- [ ] You can say out loud what each defect was
- [ ] You can say which defects the assistant found on its own and which ones only the tests caught
- [ ] You have watched the test fail at least once, on purpose
