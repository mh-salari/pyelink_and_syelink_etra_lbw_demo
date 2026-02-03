"""Pupil signal filtering and cleaning utilities."""

import numpy as np
from scipy.interpolate import PchipInterpolator
from scipy.signal import savgol_filter


def clean_pupil_signal(
    timestamps: np.ndarray, pupil: np.ndarray, blink_deriv_threshold: float = 0.05, expand_ms: int = 500,
) -> np.ndarray:
    """Standard pupil-cleaning pipeline.

    - Detect blink spikes using derivative threshold
    - Expand windows ±expand_ms
    - Remove spike samples
    - PCHIP interpolation
    - Light Savitzky-Golay smoothing
    """
    pupil = np.array(pupil, dtype=float)
    timestamps = np.array(timestamps, dtype=float)

    # ----- 1. Compute fractional derivative -----
    dp = np.diff(pupil)
    with np.errstate(divide="ignore", invalid="ignore"):
        deriv = np.abs(dp / pupil[:-1])
        deriv[~np.isfinite(deriv)] = 0  # Set NaNs/Infs from division by zero to 0
    spike_idx = np.where(deriv > blink_deriv_threshold)[0]

    # ----- 2. Make mask for blink/artifact removal -----
    mask = np.isfinite(pupil)
    if np.median(np.diff(timestamps)) > 0:
        expand_samples = int(expand_ms / np.median(np.diff(timestamps)))
    else:
        expand_samples = 0
    for i in spike_idx:
        s = max(0, i - expand_samples)
        e = min(len(mask), i + expand_samples)
        mask[s:e] = False

    # If all data is invalid after artifact removal, return NaNs
    if not np.any(mask):
        return np.full_like(pupil, np.nan)

    # ----- 3. Interpolate missing data -----
    valid_x = np.where(mask)[0]
    valid_y = pupil[mask]
    interpolator = PchipInterpolator(valid_x, valid_y)
    cleaned = interpolator(np.arange(len(pupil)))

    # ----- 4. Light smoothing -----
    return savgol_filter(cleaned, window_length=51, polyorder=2)


def expand_nan_blocks(
    timestamps: np.ndarray,
    left_pupil: np.ndarray,
    right_pupil: np.ndarray,
    min_duration_ms: int,
    expand_ms: int,
) -> tuple[np.ndarray, np.ndarray]:
    """Finds blocks of NaNs and expands them in both signals.

    If a block of NaNs is found in either pupil signal that is longer than
    `min_duration_ms`, the region is expanded by `expand_ms` in both
    directions, and both pupil signals are set to NaN in this new, larger region.

    Args:
        timestamps: Array of timestamps in milliseconds.
        left_pupil: Left pupil data.
        right_pupil: Right pupil data.
        min_duration_ms: The minimum duration of a NaN block to be expanded.
        expand_ms: The number of milliseconds to expand the NaN block.

    Returns:
        A tuple of (left_pupil, right_pupil) with expanded NaN blocks.

    """
    left_pupil_out = left_pupil.copy()
    right_pupil_out = right_pupil.copy()

    # 1. Combined mask for NaNs in either eye
    either_nan_mask = np.isnan(left_pupil_out) | np.isnan(right_pupil_out)

    if not np.any(either_nan_mask):
        return left_pupil_out, right_pupil_out

    # 2. Find start and end indices of consecutive NaN blocks
    diff = np.diff(either_nan_mask.astype(np.int8))
    starts = np.where(diff == 1)[0] + 1
    if either_nan_mask[0]:
        starts = np.insert(starts, 0, 0)

    ends = np.where(diff == -1)[0]
    if either_nan_mask[-1]:
        ends = np.append(ends, len(either_nan_mask) - 1)

    if starts.size == 0 or ends.size == 0:
        return left_pupil_out, right_pupil_out

    # 3. For long NaN blocks, create a mask to expand the NaN region
    sampling_period_ms = np.median(np.diff(timestamps))
    if sampling_period_ms <= 0:  # Avoid division by zero or invalid period
        return left_pupil_out, right_pupil_out

    expand_samples = int(expand_ms / sampling_period_ms)
    removal_mask = np.zeros_like(either_nan_mask, dtype=bool)

    for start_idx, end_idx in zip(starts, ends, strict=False):
        # Note: timestamps are in ms
        duration_ms = timestamps[end_idx] - timestamps[start_idx]
        if duration_ms >= min_duration_ms:
            s = max(0, start_idx - expand_samples)
            e = min(len(removal_mask), end_idx + 1 + expand_samples)
            removal_mask[s:e] = True

    # 4. Apply the expanded mask to both eyes' data
    if np.any(removal_mask):
        left_pupil_out[removal_mask] = np.nan
        right_pupil_out[removal_mask] = np.nan

    return left_pupil_out, right_pupil_out
