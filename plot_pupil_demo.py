"""Plot pupil size from CSV data for paper demonstration."""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from pupil_filtering import clean_pupil_signal, expand_nan_blocks

# Read the CSV file
df = pd.read_csv("data/353_1_samples.csv")

# Get timestamps
timestamps = df["timestamp"].values
time_sec = (timestamps - timestamps[0]) / 1000.0

# Extract pupil areas and replace zeros with NaN (closed eyes/blinks)
left_pupil = df["left_pupil"].replace(0.0, np.nan).values
right_pupil = df["right_pupil"].replace(0.0, np.nan).values

# Apply filtering
min_nan_block_duration_ms = 5
expand_around_nan_ms = 50

left_pupil, right_pupil = expand_nan_blocks(
    timestamps, left_pupil, right_pupil, min_duration_ms=min_nan_block_duration_ms, expand_ms=expand_around_nan_ms,
)

left_clean = clean_pupil_signal(timestamps, left_pupil)
right_clean = clean_pupil_signal(timestamps, right_pupil)

# Create figure with size 1280x400 pixels at 100 dpi = (12.8, 4.0) inches
fig, ax = plt.subplots(figsize=(12.8, 4.0), dpi=100)

# Colors for pupil data and annotations
left_color = "#C62D87"
right_color = "#315079"
cal_color = "#A569AD"
val_color = "#008E7F"

# For plotting, replace NaN with 0 to show blinks going to zero
left_pupil_plot = np.nan_to_num(left_pupil, nan=0.0)
right_pupil_plot = np.nan_to_num(right_pupil, nan=0.0)

# Plot raw data
ax.plot(time_sec, left_pupil_plot, color=left_color, linewidth=1, alpha=0.8, label="Left Eye")
ax.plot(time_sec, right_pupil_plot, color=right_color, linewidth=1, alpha=0.8, label="Right Eye")
ax.set_xlabel("Time (seconds)", fontsize=11)
ax.set_ylabel("Pupil Area (arbitrary units)", fontsize=11)
ax.legend(loc="upper left", fontsize=10)
ax.grid(True, alpha=0.3)

# Extract calibration and validation periods from mode column
cal_names = ["CAL: DARK", "CAL: BRIGHT"]
val_names = ["VAL: DARK (matched)", "VAL: BRIGHT (mismatch)", "VAL: BRIGHT (matched)", "VAL: DARK (mismatch)"]

# Get y-limits for text positioning
ymin, ymax = ax.get_ylim()
text_y = (ymin + ymax) / 2

# Extract and plot calibration periods
cal_idx = df[df["mode"] == "CALIBRATE"].index
if len(cal_idx) > 0:
    # Find contiguous mode periods
    mode_periods = []
    start = cal_idx[0]
    for i in range(1, len(cal_idx)):
        if cal_idx[i] != cal_idx[i - 1] + 1:
            mode_periods.append((start, cal_idx[i - 1]))
            start = cal_idx[i]
    mode_periods.append((start, cal_idx[-1]))

    # Trim NaNs using filtered pupil data
    cal_periods = []
    for start_idx, end_idx in mode_periods:
        period_left = left_pupil[start_idx : end_idx + 1]
        period_right = right_pupil[start_idx : end_idx + 1]
        valid_mask = ~np.isnan(period_left) | ~np.isnan(period_right)

        if np.any(valid_mask):
            valid_indices = np.where(valid_mask)[0]
            first_valid = start_idx + valid_indices[0]
            last_valid = start_idx + valid_indices[-1]
            cal_periods.append((first_valid, last_valid))

    # Plot shaded regions and labels
    for i, (start_idx, end_idx) in enumerate(cal_periods):
        start, end = time_sec[start_idx], time_sec[end_idx]
        mid = (start + end) / 2
        ax.axvspan(start, end, alpha=0.3, facecolor=cal_color, edgecolor=cal_color, linewidth=2, zorder=0)
        # Move CAL: BRIGHT label slightly higher to avoid overlap
        label_y = ymax * 0.6 if "BRIGHT" in cal_names[i] else text_y
        ax.text(
            mid,
            label_y,
            cal_names[i],
            ha="center",
            va="center",
            fontsize=10,
            fontweight="bold",
            color=cal_color,
            rotation=90,
        )

# Extract and plot validation periods
val_idx = df[df["mode"] == "VALIDATE"].index
if len(val_idx) > 0:
    # Find contiguous mode periods
    mode_periods = []
    start = val_idx[0]
    for i in range(1, len(val_idx)):
        if val_idx[i] != val_idx[i - 1] + 1:
            mode_periods.append((start, val_idx[i - 1]))
            start = val_idx[i]
    mode_periods.append((start, val_idx[-1]))

    # Trim NaNs using filtered pupil data
    val_periods = []
    for start_idx, end_idx in mode_periods:
        period_left = left_pupil[start_idx : end_idx + 1]
        period_right = right_pupil[start_idx : end_idx + 1]
        valid_mask = ~np.isnan(period_left) | ~np.isnan(period_right)

        if np.any(valid_mask):
            valid_indices = np.where(valid_mask)[0]
            first_valid = start_idx + valid_indices[0]
            last_valid = start_idx + valid_indices[-1]
            val_periods.append((first_valid, last_valid))

    # Plot shaded regions and labels
    for i, (start_idx, end_idx) in enumerate(val_periods):
        start, end = time_sec[start_idx], time_sec[end_idx]
        mid = (start + end) / 2
        ax.axvspan(start, end, alpha=0.3, facecolor=val_color, edgecolor=val_color, linewidth=2, zorder=0)
        # Move BRIGHT labels higher to avoid overlap with pupil data
        label_y = ymax * 0.7 if "BRIGHT" in val_names[i] else text_y
        ax.text(
            mid,
            label_y,
            val_names[i],
            ha="center",
            va="center",
            fontsize=9,
            fontweight="bold",
            color=val_color,
            rotation=90,
        )

# Tight layout
plt.tight_layout()

# Save as PNG
output_file = "data/pupil_size_plot.png"
plt.savefig(output_file, dpi=100, bbox_inches="tight")
print(f"Saved plot to: {output_file}")

# Also show
plt.show()
