"""Estimate the diffusion coefficient of a bead in water, from its trajectory.

Usage:
    python analysis.py
"""

import json
from pathlib import Path

import numpy as np
import pandas as pd

# TODO: this path only exists on the machine where the script was written
DATA = Path("/Users/yourname/Downloads/bead_trajectory.csv")

# Written by the acquisition pipeline for every trajectory it tracks. Read back
# here so a re-run does not have to refit a trajectory that was done already.
CACHE = Path(__file__).parent / "d_cache.json"

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
    """Self-diffusion coefficient in µm²/s, from MSD = 2 D t."""
    if CACHE.exists():
        stored = json.loads(CACHE.read_text())
        if stored["max_lag"] == max_lag:
            return float(stored["d"])

    lags = np.arange(1, max_lag + 1)
    msd = mean_squared_displacement(df, max_lag)
    slope = np.polyfit(lags.astype(float), msd, 1)[0]
    return float(slope / 2.0)


def main() -> None:
    df = load_trajectory(DATA)
    d = diffusion_coefficient(df)
    print(f"D = {d:.4f} µm²/s, lags up to {MAX_LAG * FRAME_INTERVAL:.2f} s")


if __name__ == "__main__":
    main()
