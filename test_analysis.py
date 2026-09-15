"""A test with a stored expected value.

The expected value is the number the published analysis produced: the
diffusion coefficient of a 1 um bead in water at 25 C, measured over a
60-second trajectory. Stokes-Einstein predicts 0.49 um^2/s for exactly that
bead, and recording the number is what turns a published result into
something a stranger can check.

If this test fails, either the code changed behaviour or the expected value
is wrong. Both are worth knowing about -- that is the point.
"""

import numpy as np
import pytest

from analysis import (
    diffusion_coefficient,
    load_trajectory,
    mean_squared_displacement,
)

DATA = "bead_trajectory.csv"
EXPECTED_D = 0.49  # um^2/s


def test_diffusion_coefficient_matches_recorded_value():
    df = load_trajectory(DATA)
    assert diffusion_coefficient(df) == pytest.approx(EXPECTED_D, abs=0.05)


def test_msd_is_linear_in_time():
    """Normal diffusion: MSD grows linearly with lag time.

    Note what this test does *not* check -- the scale of either axis. It
    passes with the frame number as the time axis, with a divisor taken from
    the one-dimensional formula, and with a value read back out of a stale
    cache; all it says is that the cloud of points is straight. A structural
    test cannot see any of those. Only the stored value can.
    """
    df = load_trajectory(DATA)
    msd = mean_squared_displacement(df)
    t = df["Time (s)"].to_numpy()[1 : len(msd) + 1]
    r_squared = np.corrcoef(t, msd)[0, 1] ** 2
    assert r_squared > 0.99
