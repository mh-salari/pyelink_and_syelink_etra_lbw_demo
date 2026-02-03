"""Dark/Light Adaptation Example using Pyglet backend.

This example demonstrates a dark/light adaptation protocol:
- Calibrate in dark background
- Validate in bright and dark backgrounds
- Recalibrate in bright background
- Validate in dark and bright backgrounds
"""

import io

import pyglet
from jva_capture import JVACapture

import pyelink as el
from pyelink.calibration.targets import generate_target


def smooth_transition(
    tracker: el.EyeLink,
    start_color: tuple[int, int, int],
    end_color: tuple[int, int, int],
    duration: float = 5.0,
    fps: int = 60,
) -> None:
    """Smoothly transition from one background color to another.

    Args:
        tracker: EyeLink tracker instance
        start_color: Starting background color as RGB tuple (0-255)
        end_color: Ending background color as RGB tuple (0-255)
        duration: Transition duration in seconds
        fps: Frames per second for smooth animation

    """
    num_frames = int(duration * fps)
    frame_duration = duration / num_frames

    for frame in range(num_frames + 1):
        # Linear interpolation between start and end colors
        t = frame / num_frames  # Progress from 0.0 to 1.0
        current_color = (
            int(start_color[0] + (end_color[0] - start_color[0]) * t),
            int(start_color[1] + (end_color[1] - start_color[1]) * t),
            int(start_color[2] + (end_color[2] - start_color[2]) * t),
        )

        # Set clear color for pyglet (normalized to 0.0-1.0)
        pyglet.gl.glClearColor(
            current_color[0] / 255.0,
            current_color[1] / 255.0,
            current_color[2] / 255.0,
            1.0,
        )

        tracker.window.clear()
        tracker.window.flip()
        tracker.wait(frame_duration)


def show_countdown(
    tracker: el.EyeLink,
    duration: int,
    bg_color: tuple[int, int, int] = (0, 0, 0),
    text_color: tuple[int, int, int, int] = (128, 128, 128, 255),
    fixation_duration: float = 2.5,
) -> None:
    """Show countdown with specified background and text colors.

    Args:
        tracker: EyeLink tracker instance
        duration: Duration in seconds
        bg_color: Background color as RGB tuple (0-255)
        text_color: Text color as RGBA tuple (0-255)
        fixation_duration: Duration to show fixation target after countdown (seconds)

    """
    # Set clear color for pyglet (normalized to 0.0-1.0)
    pyglet.gl.glClearColor(bg_color[0] / 255.0, bg_color[1] / 255.0, bg_color[2] / 255.0, 1.0)

    for i in range(duration, 0, -1):
        tracker.window.clear()
        label = pyglet.text.Label(
            str(i),
            font_name="Arial",
            font_size=10,
            x=tracker.window.width // 2,
            y=tracker.window.height // 2,
            anchor_x="center",
            anchor_y="center",
            color=text_color,
        )
        label.draw()
        tracker.window.flip()
        tracker.wait(1)  # Use tracker.wait() instead of time.sleep() to keep event loop active

    # Show fixation target at center for specified duration
    if fixation_duration > 0:
        # Generate the same target used in calibration
        pil_image = generate_target(tracker.settings)
        buffer = io.BytesIO()
        pil_image.save(buffer, format="PNG")
        buffer.seek(0)
        img = pyglet.image.load("target.png", file=buffer)
        img.anchor_x = img.width // 2
        img.anchor_y = img.height // 2
        target_sprite = pyglet.sprite.Sprite(img)

        # Position at center of screen
        target_sprite.x = tracker.window.width // 2
        target_sprite.y = tracker.window.height // 2

        # Draw and display
        tracker.window.clear()
        target_sprite.draw()
        tracker.window.flip()
        tracker.wait(fixation_duration)


# Configure tracker with gray fixation target (transparent cross)
settings = el.Settings(
    backend="pyglet",
    fullscreen=True,
    # host_ip="dummy",  # Use dummy mode for testing without EyeLink
    display_index=0,
    enable_long_filenames=True,
    filename="404_3",
    filepath="./data/",  # Directory where EDF file will be saved
    eye_tracked="BOTH",  # or "RIGHT" or "BOTH"
    # Gray fixation target with transparent cross
    fixation_center_color=(128, 128, 128, 255),  # Gray center
    fixation_outer_color=(128, 128, 128, 255),  # Gray outer ring
    fixation_cross_color=(128, 128, 128, 0),  # Transparent cross (alpha=0)
    calibration_text_font_size=10,
    # calibration_area_proportion=(0.9 * 0.88, 0.9 * 0.83),
    # validation_area_proportion=(0.9 * 0.88, 0.9 * 0.83),
    # calibration_corner_scaling=0.75,
    # validation_corner_scaling=0.75,
)


dark_adaptation_duration = 30  # Duration of dark adaptation periods in seconds
bright_adaptation_duration = 15  # Duration of bright adaptation periods in seconds

print("Connecting to EyeLink and creating window...")
tracker = el.EyeLink(settings, record_raw_data=True)

capture = JVACapture(f"{tracker.settings.filepath}{tracker.settings.filename}.mkv")

# Register cleanup to stop screen capture before exit
tracker.register_cleanup(capture.stop)

print("Starting screen capture...")
capture.start()

print("\n=== Step 0: Camera calibration ===")
tracker.camera_setup()

# Step 1: Smooth transition from GRAY to DARK
print("\n=== Step 1: Transitioning from GRAY to DARK (5s) ===")
tracker.start_recording()
smooth_transition(tracker, start_color=(128, 128, 128), end_color=(0, 0, 0), duration=5.0)
tracker.stop_recording()

# Step 2: DARK adaptation
print("\n=== Step 2: DARK adaptation ===")
tracker.start_recording()
show_countdown(tracker, dark_adaptation_duration, bg_color=(0, 0, 0))
tracker.stop_recording()

# Step 3: Calibrate in DARK
print("\n=== Step 3: CALIBRATE IN DARK ===")
print("Press 'C' to calibrate, then Enter to accept")
tracker.settings.cal_background_color = (0, 0, 0)  # Black
tracker.settings.calibration_text_color = (255, 255, 255)  # White
tracker.settings.calibration_instruction_text = "calibrate"
tracker.calibrate(record_samples=True, mode="calibration-only")

# Step 4: Validate in DARK
print("\n=== Step 4: VALIDATE IN DARK ===")
print("Press 'V' to validate, then Enter to accept")
tracker.settings.cal_background_color = (0, 0, 0)  # Black
tracker.settings.calibration_text_color = (255, 255, 255)  # White
tracker.settings.calibration_instruction_text = "validate"
tracker.calibrate(record_samples=True, mode="validation-only")

# Step 5: Smooth transition from DARK to BRIGHT
print("\n=== Step 5: Transitioning from DARK to BRIGHT (5s) ===")
tracker.start_recording()
smooth_transition(tracker, start_color=(0, 0, 0), end_color=(255, 255, 255), duration=5.0)
tracker.stop_recording()

# Step 6: BRIGHT adaptation
print("\n=== Step 6: BRIGHT adaptation ===")
tracker.start_recording()
show_countdown(tracker, bright_adaptation_duration, bg_color=(255, 255, 255), text_color=(0, 0, 0, 255))
tracker.stop_recording()

# Step 7: Validate in BRIGHT
print("\n=== Step 7: VALIDATE IN BRIGHT ===")
print("Press 'V' to validate, then Enter to accept")
tracker.settings.cal_background_color = (255, 255, 255)  # White
tracker.settings.calibration_text_color = (0, 0, 0)  # Black
tracker.settings.calibration_instruction_text = "validate"
tracker.calibrate(record_samples=True, mode="validation-only")

# Step 8: Calibrate in BRIGHT
print("\n=== Step 8: CALIBRATE IN BRIGHT ===")
print("Press 'C' to calibrate, then Enter to accept")
tracker.settings.cal_background_color = (255, 255, 255)  # White
tracker.settings.calibration_text_color = (0, 0, 0)  # Black
tracker.settings.calibration_instruction_text = "calibrate"
tracker.calibrate(record_samples=True, mode="calibration-only")

# Step 9: Validate in BRIGHT
print("\n=== Step 9: VALIDATE IN BRIGHT ===")
print("Press 'V' to validate, then Enter to accept")
tracker.settings.cal_background_color = (255, 255, 255)  # White
tracker.settings.calibration_text_color = (0, 0, 0)  # Black
tracker.settings.calibration_instruction_text = "validate"
tracker.calibrate(record_samples=True, mode="validation-only")

# Step 10: Smooth transition from BRIGHT to DARK
print("\n=== Step 10: Transitioning from BRIGHT to DARK (5s) ===")
tracker.start_recording()
smooth_transition(tracker, start_color=(255, 255, 255), end_color=(0, 0, 0), duration=5.0)
tracker.stop_recording()

# Step 11: DARK adaptation
print("\n=== Step 11: DARK adaptation ===")
tracker.start_recording()
show_countdown(tracker, dark_adaptation_duration, bg_color=(0, 0, 0))
tracker.stop_recording()

# Step 12: Validate in DARK
print("\n=== Step 12: VALIDATE IN DARK ===")
print("Press 'V' to validate, then Enter to accept")
tracker.settings.cal_background_color = (0, 0, 0)  # Black
tracker.settings.calibration_text_color = (255, 255, 255)  # White
tracker.settings.calibration_instruction_text = "validate"
tracker.calibrate(record_samples=True, mode="validation-only")

# Clean up
print("\n=== Experiment Complete ===")
tracker.end_experiment()
