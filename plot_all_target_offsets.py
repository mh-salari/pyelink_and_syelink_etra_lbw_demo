"""Plot all target offsets for all validations - matching vs. mismatching conditions."""

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from pyelink import Settings
from pyelink.calibration.targets import generate_target

# Padding around screen edges (pixels)
SCREEN_PADDING = 150


def load_session(filename, data_dir):
    """Load session data from JSON file."""
    filepath = data_dir / filename
    with open(filepath) as f:
        return json.load(f)


def get_all_offsets(validation):
    """Extract all point offsets for both eyes, organized by point number."""
    offsets = {}

    for point in validation.get("points", []):
        point_num = point["point_number"]
        if point_num not in offsets:
            offsets[point_num] = {"left": None, "right": None}

        offset = [point["offset_pix_x"], point["offset_pix_y"]]
        if point["eye"] == "LEFT":
            offsets[point_num]["left"] = offset
        elif point["eye"] == "RIGHT":
            offsets[point_num]["right"] = offset

    return offsets


def get_avg_error_deg(validation):
    """Extract average error in degrees for both eyes from validation."""
    left_err = validation.get("summary_left", {}).get("error_avg_deg")
    right_err = validation.get("summary_right", {}).get("error_avg_deg")
    return left_err, right_err


def normalize_position(target_x, target_y, screen_width, screen_height):
    """Normalize target position to plot coordinates (centered at 0,0)."""
    norm_x = target_x - screen_width / 2
    norm_y = target_y - screen_height / 2
    return norm_x, norm_y


def plot_all_sessions(session_files, data_dir, output_file):
    """Plot all target offsets for all validations from all sessions on two side-by-side plots."""
    # Load first session to get screen dimensions and target positions
    first_session = load_session(session_files[0], data_dir)
    display_coords = first_session.get("display_coords", {})
    screen_width = display_coords.get("right", 1279) - display_coords.get("left", 0) + 1
    screen_height = display_coords.get("bottom", 1023) - display_coords.get("top", 0) + 1

    # Get target positions from first validation's targets
    validations = first_session.get("validations", [])
    target_positions = {}
    if validations and "targets" in validations[0]:
        targets_data = validations[0]["targets"].get("targets", [])
        for idx, pos in enumerate(targets_data):
            target_positions[idx] = tuple(pos)

    # Validation conditions from experiment protocol (dark_light_adaptation_2.py):
    # 1. Calibrate DARK → Validate DARK (matched)
    # 2. Transition BRIGHT → Validate BRIGHT (not matched - dark cal)
    # 3. Calibrate BRIGHT → Validate BRIGHT (matched)
    # 4. Transition DARK → Validate DARK (not matched - bright cal)

    # Colors based on VALIDATION background: dark gray for dark, gold for bright
    val_colors = ["dimgray", "gold", "gold", "dimgray"]

    # Markers: circle for matched, square for not matched
    val_markers = ["o", "s", "o", "s"]

    fig, (ax_matched, ax_notmatched) = plt.subplots(1, 2, figsize=(14, 6.5))

    # Collect error degrees for title
    matched_dark_errors = []  # Val#1
    matched_bright_errors = []  # Val#3
    notmatched_bright_errors = []  # Val#2
    notmatched_dark_errors = []  # Val#4

    # Store all session data first
    all_session_data = []

    for sess_idx, session_file in enumerate(session_files):
        session = load_session(session_file, data_dir)
        validations = session.get("validations", [])

        session_data = []
        for i, val in enumerate(validations):
            if i >= 4:
                break

            offsets = get_all_offsets(val)
            left_err, right_err = get_avg_error_deg(val)

            # Collect errors by condition
            if left_err is not None:
                if i == 0:
                    matched_dark_errors.append(left_err)
                elif i == 1:
                    notmatched_bright_errors.append(left_err)
                elif i == 2:
                    matched_bright_errors.append(left_err)
                elif i == 3:
                    notmatched_dark_errors.append(left_err)
            if right_err is not None:
                if i == 0:
                    matched_dark_errors.append(right_err)
                elif i == 1:
                    notmatched_bright_errors.append(right_err)
                elif i == 2:
                    matched_bright_errors.append(right_err)
                elif i == 3:
                    notmatched_dark_errors.append(right_err)

            session_data.append(offsets)

        all_session_data.append(session_data)

    # Calculate average errors for titles
    avg_matched_dark = np.mean(matched_dark_errors) if matched_dark_errors else 0
    avg_matched_bright = np.mean(matched_bright_errors) if matched_bright_errors else 0
    avg_notmatched_dark = np.mean(notmatched_dark_errors) if notmatched_dark_errors else 0
    avg_notmatched_bright = np.mean(notmatched_bright_errors) if notmatched_bright_errors else 0

    # Plot data on both subplots
    for sess_idx, session_data in enumerate(all_session_data):
        for val_idx, offsets in enumerate(session_data):
            # Determine which subplot to use
            if val_idx in [0, 2]:  # Matched (Val#1 and Val#3)
                ax = ax_matched
            else:  # Not matched (Val#2 and Val#4)
                ax = ax_notmatched

            # Plot each target point
            for point_num, point_offsets in offsets.items():
                # Get normalized target position
                if point_num in target_positions:
                    target_x, target_y = target_positions[point_num]
                    base_x, base_y = normalize_position(target_x, target_y, screen_width, screen_height)
                else:
                    continue  # Skip unknown points

                left_offset = point_offsets.get("left")
                right_offset = point_offsets.get("right")

                # Plot left eye offset
                if left_offset:
                    plot_x = base_x + left_offset[0]
                    plot_y = base_y + left_offset[1]
                    ax.scatter(
                        plot_x,
                        plot_y,
                        s=30,
                        c=val_colors[val_idx],
                        marker=val_markers[val_idx],
                        alpha=0.7,
                        edgecolors="black",
                        linewidths=0.5,
                    )
                    ax.annotate(
                        "L",
                        (plot_x, plot_y),
                        xytext=(2, 2),
                        textcoords="offset points",
                        fontsize=5,
                        fontweight="bold",
                        alpha=0.7,
                    )

                # Plot right eye offset
                if right_offset:
                    plot_x = base_x + right_offset[0]
                    plot_y = base_y + right_offset[1]
                    ax.scatter(
                        plot_x,
                        plot_y,
                        s=30,
                        c=val_colors[val_idx],
                        marker=val_markers[val_idx],
                        alpha=0.7,
                        edgecolors="black",
                        linewidths=0.5,
                    )
                    ax.annotate(
                        "R",
                        (plot_x, plot_y),
                        xytext=(2, 2),
                        textcoords="offset points",
                        fontsize=5,
                        fontweight="bold",
                        alpha=0.7,
                    )

                # Plot average offset
                if left_offset and right_offset:
                    avg_offset_x = (left_offset[0] + right_offset[0]) / 2
                    avg_offset_y = (left_offset[1] + right_offset[1]) / 2
                    plot_x = base_x + avg_offset_x
                    plot_y = base_y + avg_offset_y
                    ax.scatter(
                        plot_x,
                        plot_y,
                        s=20,
                        c=val_colors[val_idx],
                        marker="x",
                        alpha=0.7,
                        linewidths=1,
                    )

        # Draw lines between paired validations for each target
        if len(session_data) >= 4:
            for point_num in target_positions:
                if point_num in target_positions:
                    target_x, target_y = target_positions[point_num]
                    base_x, base_y = normalize_position(target_x, target_y, screen_width, screen_height)

                    # For each eye type (left, right, avg)
                    for eye_type in ["left", "right", "avg"]:
                        # Get offsets for matched pair (Val#0 and Val#2)
                        if point_num in session_data[0] and point_num in session_data[2]:
                            off0 = session_data[0][point_num].get(eye_type) if eye_type != "avg" else None
                            off2 = session_data[2][point_num].get(eye_type) if eye_type != "avg" else None

                            # Calculate avg if needed
                            if eye_type == "avg":
                                left0 = session_data[0][point_num].get("left")
                                right0 = session_data[0][point_num].get("right")
                                left2 = session_data[2][point_num].get("left")
                                right2 = session_data[2][point_num].get("right")
                                if left0 and right0:
                                    off0 = [(left0[0] + right0[0]) / 2, (left0[1] + right0[1]) / 2]
                                if left2 and right2:
                                    off2 = [(left2[0] + right2[0]) / 2, (left2[1] + right2[1]) / 2]

                            if off0 and off2:
                                ax_matched.plot(
                                    [base_x + off0[0], base_x + off2[0]],
                                    [base_y + off0[1], base_y + off2[1]],
                                    c="green",
                                    alpha=0.4,
                                    linewidth=0.8,
                                    linestyle="--",
                                )

                        # Get offsets for not-matched pair (Val#1 and Val#3)
                        if point_num in session_data[1] and point_num in session_data[3]:
                            off1 = session_data[1][point_num].get(eye_type) if eye_type != "avg" else None
                            off3 = session_data[3][point_num].get(eye_type) if eye_type != "avg" else None

                            # Calculate avg if needed
                            if eye_type == "avg":
                                left1 = session_data[1][point_num].get("left")
                                right1 = session_data[1][point_num].get("right")
                                left3 = session_data[3][point_num].get("left")
                                right3 = session_data[3][point_num].get("right")
                                if left1 and right1:
                                    off1 = [(left1[0] + right1[0]) / 2, (left1[1] + right1[1]) / 2]
                                if left3 and right3:
                                    off3 = [(left3[0] + right3[0]) / 2, (left3[1] + right3[1]) / 2]

                            if off1 and off3:
                                ax_notmatched.plot(
                                    [base_x + off1[0], base_x + off3[0]],
                                    [base_y + off1[1], base_y + off3[1]],
                                    c="red",
                                    alpha=0.4,
                                    linewidth=0.8,
                                    linestyle="--",
                                )

    # Generate target image for display at each location
    settings = Settings(
        fixation_center_color=(128, 128, 128, 255),
        fixation_outer_color=(128, 128, 128, 255),
        fixation_cross_color=(128, 128, 128, 0),
    )
    target_img = generate_target(settings, target_type="ABC")
    target_array = np.array(target_img)
    img_height, img_width = target_array.shape[:2]

    # Draw black rectangle showing screen boundaries
    screen_half_w = screen_width / 2
    screen_half_h = screen_height / 2
    from matplotlib.patches import Rectangle

    for ax in [ax_matched, ax_notmatched]:
        screen_rect = Rectangle(
            (-screen_half_w, -screen_half_h),
            screen_width,
            screen_height,
            linewidth=2,
            edgecolor="black",
            facecolor="none",
            zorder=0,
        )
        ax.add_patch(screen_rect)

    # Plot target at each position
    for point_num, (target_x, target_y) in target_positions.items():
        norm_x, norm_y = normalize_position(target_x, target_y, screen_width, screen_height)
        extent = [
            norm_x - img_width / 2,
            norm_x + img_width / 2,
            norm_y - img_height / 2,
            norm_y + img_height / 2,
        ]
        for ax in [ax_matched, ax_notmatched]:
            ax.imshow(target_array, extent=extent, zorder=1)

    # Configure matched plot
    ax_matched.set_xlabel("X position (pixels from screen center)", fontsize=11)
    ax_matched.set_ylabel("Y position (pixels from screen center)", fontsize=11)
    ax_matched.set_title(
        f"MATCHED\nDark: {avg_matched_dark:.2f}°  |  Bright: {avg_matched_bright:.2f}°", fontsize=12, fontweight="bold",
    )
    ax_matched.grid(True, alpha=0.2)
    ax_matched.set_aspect("equal")
    ax_matched.set_xlim(-screen_half_w - SCREEN_PADDING, screen_half_w + SCREEN_PADDING)
    ax_matched.set_ylim(-screen_half_h - SCREEN_PADDING, screen_half_h + SCREEN_PADDING)

    # Configure not matched plot
    ax_notmatched.set_xlabel("X position (pixels from screen center)", fontsize=11)
    ax_notmatched.set_ylabel("Y position (pixels from screen center)", fontsize=11)
    ax_notmatched.set_title(
        f"NOT MATCHED\nDark: {avg_notmatched_dark:.2f}°  |  Bright: {avg_notmatched_bright:.2f}°",
        fontsize=12,
        fontweight="bold",
    )
    ax_notmatched.grid(True, alpha=0.2)
    ax_notmatched.set_aspect("equal")
    ax_notmatched.set_xlim(-screen_half_w - SCREEN_PADDING, screen_half_w + SCREEN_PADDING)
    ax_notmatched.set_ylim(-screen_half_h - SCREEN_PADDING, screen_half_h + SCREEN_PADDING)

    fig.suptitle("All Target Validation Offsets - All Sessions", fontsize=14, fontweight="bold")
    fig.tight_layout()

    plt.savefig(output_file, dpi=150)
    print(f"Saved plot: {output_file}")
    plt.show()
    plt.close()


def main():
    """Generate combined plot for all sessions."""
    # Use relative path - data directory next to this script
    script_dir = Path(__file__).parent
    data_dir = script_dir / "data"

    # Auto-detect all JSON files in data directory
    json_files = sorted(data_dir.glob("*.json"))
    if not json_files:
        print(f"Error: No JSON files found in {data_dir}")
        return

    session_files = [f.name for f in json_files]
    print(f"Found {len(session_files)} JSON file(s): {', '.join(session_files)}")

    # Output file in data directory
    output_file = data_dir / "all_target_offsets.png"

    print("Generating plot...")
    plot_all_sessions(session_files, data_dir, output_file)


if __name__ == "__main__":
    main()
