"""JVA01-Capture screen recording module.

This module provides a simple interface to record from the JVA01-Capture device
using ffmpeg-python. The device appears as an AVFoundation video device on macOS.
"""

import re
import subprocess
import time
from pathlib import Path
from types import TracebackType

import ffmpeg


class JVACapture:
    """Screen capture from JVA01-Capture device.

    Usage:
        capture = JVACapture("output.mkv")
        capture.start()
        # ... run your experiment ...
        capture.stop()

    Or use as context manager:
        with JVACapture("output.mkv") as capture:
            # ... run your experiment ...
    """

    @staticmethod
    def find_device(device_name: str = "JVA01-Capture") -> int:
        """Find AVFoundation device index by name.

        Args:
            device_name: Name of the capture device to find

        Returns:
            Device index

        Raises:
            RuntimeError: If device not found

        """
        try:
            # List all AVFoundation devices
            result = subprocess.run(
                ["ffmpeg", "-f", "avfoundation", "-list_devices", "true", "-i", ""],  # noqa: S607
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
            # ffmpeg outputs device list to stderr
            output = result.stderr

            # Parse device list looking for our device
            # Format: [AVFoundation indev @ 0x...] [0] JVA01-Capture
            pattern = rf"\[(\d+)\]\s+{re.escape(device_name)}"
            match = re.search(pattern, output)

            if match:
                return int(match.group(1))

            raise RuntimeError(f"Device '{device_name}' not found.\nAvailable devices:\n{output}")

        except subprocess.TimeoutExpired as err:
            raise RuntimeError("Timeout while listing AVFoundation devices") from err
        except FileNotFoundError as err:
            raise RuntimeError("ffmpeg not found. Please install ffmpeg.") from err

    def __init__(
        self,
        output_path: str,
        device_name: str = "JVA01-Capture",
        framerate: int = 60,
        preset: str = "medium",
    ) -> None:
        """Initialize capture settings.

        Args:
            output_path: Path where video file will be saved
            device_name: Name of AVFoundation device
            framerate: Recording framerate (default: 60 fps)
            preset: ffmpeg encoding preset (ultrafast, fast, medium, slow)

        """
        self.output_path = Path(output_path).resolve()
        self.device_index = self.find_device(device_name)
        self.framerate = framerate
        self.preset = preset
        self.process = None

        # Create output directory if it doesn't exist
        self.output_path.parent.mkdir(parents=True, exist_ok=True)

        print(f"Found {device_name} at device index {self.device_index}")

    def start(self) -> None:
        """Start recording from JVA01-Capture device."""
        if self.process is not None:
            print("Warning: Capture already running")
            return

        stream = (
            ffmpeg.input(
                f"{self.device_index}",
                format="avfoundation",
                framerate=self.framerate,
                thread_queue_size=512,
                probesize=32,
                analyzeduration=0,
            )
            .output(
                str(self.output_path),
                vcodec="libx264",
                preset=self.preset,
                pix_fmt="yuv420p",
                r=self.framerate,
                vsync="cfr",
            )
            .overwrite_output()
        )

        self.process = stream.run_async(pipe_stdin=True, pipe_stderr=True)

        # Give ffmpeg a moment to initialize
        time.sleep(0.5)

        # Check if process started successfully
        if self.process.poll() is not None:
            self.process = None
            raise RuntimeError(
                f"FFmpeg failed to start. Check that JVA01-Capture is connected.\nOutput path: {self.output_path}",
            )

        print(f"Recording started: {self.output_path}")

    def stop(self) -> None:
        """Stop recording and finalize video file."""
        if self.process is None:
            print("Warning: No capture process running")
            return

        print("Stopping recording and finalizing video...")

        try:
            if self.process.stdin and not self.process.stdin.closed:
                self.process.stdin.write(b"q")
                self.process.stdin.flush()
                self.process.stdin.close()

            return_code = self.process.wait(timeout=30)

            if return_code != 0:
                stderr = self.process.stderr.read() if self.process.stderr else b""
                print(f"Warning: FFmpeg exited with code {return_code}")
                if stderr:
                    print(f"FFmpeg stderr: {stderr.decode('utf-8', errors='ignore')}")

        except subprocess.TimeoutExpired:
            print("Warning: FFmpeg didn't stop gracefully, sending SIGTERM...")
            self.process.terminate()
            try:
                self.process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                print("Warning: FFmpeg didn't respond to SIGTERM, killing process...")
                self.process.kill()
                self.process.wait()
        except Exception as e:
            print(f"Warning: Error during graceful stop: {e}")
            self.process.terminate()
            try:
                self.process.wait(timeout=3)
            except Exception:
                self.process.kill()
                self.process.wait()

        self.process = None
        print(f"Recording stopped: {self.output_path}")

    def __enter__(self) -> "JVACapture":
        """Context manager entry."""
        self.start()
        return self

    def __exit__(
        self,
        _exc_type: type[BaseException] | None,
        _exc_val: BaseException | None,
        _exc_tb: TracebackType | None,
    ) -> bool:
        """Context manager exit."""
        self.stop()
        return False

    def __del__(self) -> None:
        """Cleanup on deletion."""
        if self.process is not None:
            self.stop()
