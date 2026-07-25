#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
utils.py
=========
Shared utility functions and helpers for the Shelter Inspection System.

Provides:
    • Logging configuration (console + optional file handler).
    • Timing decorators and context managers.
    • Geometry helpers (distance, angle, coordinate transforms).
    • File I/O utilities.
    • Terminal display helpers.
    • System information display.

Author  : Team LiDAR-Inspect
Project : 3D LiDAR-Based Shelter Damage Inspection System
License : MIT
"""

import os
import sys
import math
import time
import logging

# ---------------------------------------------------------------------------
# Force UTF-8 output on Windows so box-drawing / Unicode chars render correctly
# ---------------------------------------------------------------------------
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
import logging.handlers
import platform
import functools
from datetime import datetime, timezone
from contextlib import contextmanager
from typing import Callable, Any, Tuple, Optional, Generator

# ---------------------------------------------------------------------------
# ANSI Colour Codes (terminal styling)
# ---------------------------------------------------------------------------
RESET   = "\033[0m"
BOLD    = "\033[1m"
DIM     = "\033[2m"
CYAN    = "\033[96m"
GREEN   = "\033[92m"
YELLOW  = "\033[93m"
ORANGE  = "\033[33m"
RED     = "\033[91m"
MAGENTA = "\033[95m"
WHITE   = "\033[97m"


# ---------------------------------------------------------------------------
# Logging Setup
# ---------------------------------------------------------------------------

def setup_logging(
    level: int = logging.INFO,
    log_file: Optional[str] = None,
    log_format: str = "%(asctime)s | %(levelname)-8s | %(name)-30s | %(message)s",
) -> logging.Logger:
    """
    Configure the root logger with console and optional rotating file handlers.

    Args:
        level      : Minimum log level (e.g. logging.DEBUG, logging.INFO).
        log_file   : If provided, logs are also written to this rotating file.
        log_format : Format string for log messages.

    Returns:
        logging.Logger: The configured root logger.
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Remove any existing handlers to prevent duplicate log output
    if root_logger.handlers:
        root_logger.handlers.clear()

    # Console handler with colour-coded levels
    ch = logging.StreamHandler()
    ch.setLevel(level)
    ch.setFormatter(ColoredFormatter(log_format))
    root_logger.addHandler(ch)

    # Optional rotating file handler
    if log_file:
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        fh = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes  = 5 * 1024 * 1024,   # 5 MB per file
            backupCount = 3,
            encoding  = "utf-8",
        )
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(logging.Formatter(log_format))
        root_logger.addHandler(fh)
        logging.getLogger(__name__).info("Log file: %s", log_file)

    return root_logger


class ColoredFormatter(logging.Formatter):
    """
    Custom logging formatter that adds ANSI colour codes based on log level.

    Makes it easy to visually distinguish log severity in the terminal during
    long robot inspection runs.
    """

    LEVEL_COLORS = {
        logging.DEBUG   : DIM,
        logging.INFO    : GREEN,
        logging.WARNING : YELLOW,
        logging.ERROR   : RED,
        logging.CRITICAL: MAGENTA,
    }

    def format(self, record: logging.LogRecord) -> str:
        """Override to inject colour codes around the level name."""
        color      = self.LEVEL_COLORS.get(record.levelno, RESET)
        record.levelname = f"{color}{record.levelname:<8}{RESET}"
        return super().format(record)


# ---------------------------------------------------------------------------
# Timing Utilities
# ---------------------------------------------------------------------------

def timeit(func: Callable) -> Callable:
    """
    Decorator that measures and logs the execution time of a function.

    Usage:
        @timeit
        def my_slow_function():
            ...

    Args:
        func : The function to decorate.

    Returns:
        Callable: Wrapped function that logs its runtime.
    """
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        t0     = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed= time.perf_counter() - t0
        logging.getLogger(func.__module__).debug(
            "%s() completed in %.4f s", func.__qualname__, elapsed
        )
        return result
    return wrapper


@contextmanager
def timer(label: str = "block") -> Generator:
    """
    Context manager for timing an arbitrary code block.

    Usage:
        with timer("point cloud generation"):
            ...

    Args:
        label : Human-readable name for the timed block.

    Yields:
        None
    """
    logger = logging.getLogger(__name__)
    t0 = time.perf_counter()
    try:
        yield
    finally:
        elapsed = time.perf_counter() - t0
        logger.info("⏱  %s : %.4f s", label, elapsed)


# ---------------------------------------------------------------------------
# Geometry Helpers
# ---------------------------------------------------------------------------

def euclidean_distance(
    p1: Tuple[float, float, float],
    p2: Tuple[float, float, float],
) -> float:
    """
    Compute the 3D Euclidean distance between two points.

    Args:
        p1 : (x, y, z) tuple.
        p2 : (x, y, z) tuple.

    Returns:
        float: Distance in the same units as the input coordinates.
    """
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(p1, p2)))


def euclidean_distance_2d(
    p1: Tuple[float, float],
    p2: Tuple[float, float],
) -> float:
    """
    Compute the 2D Euclidean distance (ignoring Z axis).

    Args:
        p1 : (x, y) tuple.
        p2 : (x, y) tuple.

    Returns:
        float: 2D distance.
    """
    return math.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2)


def angle_between_vectors(
    v1: Tuple[float, float, float],
    v2: Tuple[float, float, float],
) -> float:
    """
    Compute the angle (in degrees) between two 3D vectors.

    Uses the dot-product formula:  θ = arccos(v1·v2 / (|v1||v2|))

    Args:
        v1 : First vector as (x, y, z).
        v2 : Second vector as (x, y, z).

    Returns:
        float: Angle in degrees [0, 180].
    """
    dot    = sum(a * b for a, b in zip(v1, v2))
    mag_v1 = math.sqrt(sum(a ** 2 for a in v1))
    mag_v2 = math.sqrt(sum(b ** 2 for b in v2))
    cosine = dot / (mag_v1 * mag_v2 + 1e-12)
    cosine = max(-1.0, min(1.0, cosine))   # Numerical clamp
    return math.degrees(math.acos(cosine))


def deg_to_rad(degrees: float) -> float:
    """Convert degrees to radians."""
    return degrees * (math.pi / 180.0)


def rad_to_deg(radians: float) -> float:
    """Convert radians to degrees."""
    return radians * (180.0 / math.pi)


def normalize_angle(angle_rad: float) -> float:
    """
    Normalise an angle to the range [-π, π].

    Args:
        angle_rad : Input angle in radians.

    Returns:
        float: Normalised angle in [-π, π].
    """
    return (angle_rad + math.pi) % (2 * math.pi) - math.pi


def polar_to_cartesian(
    r: float,
    theta: float,
    z: float = 0.0,
) -> Tuple[float, float, float]:
    """
    Convert polar (r, θ) coordinates to Cartesian (x, y, z).

    Args:
        r     : Radial distance.
        theta : Azimuth angle in radians.
        z     : Elevation (default 0.0).

    Returns:
        Tuple[float, float, float]: (x, y, z) Cartesian coordinates.
    """
    return (r * math.cos(theta), r * math.sin(theta), z)


def cartesian_to_polar(
    x: float,
    y: float,
) -> Tuple[float, float]:
    """
    Convert 2D Cartesian (x, y) to polar (r, θ).

    Args:
        x : X-coordinate.
        y : Y-coordinate.

    Returns:
        Tuple[float, float]: (range, azimuth_rad)
    """
    r     = math.sqrt(x ** 2 + y ** 2)
    theta = math.atan2(y, x)
    return r, theta


# ---------------------------------------------------------------------------
# File I/O Utilities
# ---------------------------------------------------------------------------

def ensure_directory(path: str) -> str:
    """
    Create a directory (and all parents) if it does not exist.

    Args:
        path : Target directory path.

    Returns:
        str: The same path, for use in chained expressions.
    """
    os.makedirs(path, exist_ok=True)
    return path


def save_text_file(
    content: str,
    filepath: str,
    encoding: str = "utf-8",
) -> bool:
    """
    Write text content to a file, creating parent directories as needed.

    Args:
        content  : String content to write.
        filepath : Destination file path.
        encoding : File encoding (default UTF-8).

    Returns:
        bool: True if successful, False on error.
    """
    logger = logging.getLogger(__name__)
    try:
        ensure_directory(os.path.dirname(filepath))
        with open(filepath, "w", encoding=encoding) as fh:
            fh.write(content)
        logger.info("File saved → %s (%d bytes)", filepath, len(content.encode(encoding)))
        return True
    except OSError as exc:
        logger.error("Failed to save file '%s': %s", filepath, exc)
        return False


# ---------------------------------------------------------------------------
# Terminal Display Helpers
# ---------------------------------------------------------------------------

def print_banner(title: str, width: int = 68) -> None:
    """
    Print a styled ASCII banner to the terminal.

    Args:
        title : Text to display inside the banner.
        width : Total banner width in characters.
    """
    pad   = (width - len(title) - 2) // 2
    line  = "═" * width
    print(f"\n{BOLD}{CYAN}{line}")
    print(f"║{' ' * pad}{title}{' ' * (width - pad - len(title) - 2)}║")
    print(f"{line}{RESET}\n")


def print_step(step: int, total: int, description: str) -> None:
    """
    Print a formatted pipeline step indicator.

    Args:
        step        : Current step number.
        total       : Total number of steps.
        description : Step description label.
    """
    pct   = int((step / total) * 20)
    bar   = "▓" * pct + "░" * (20 - pct)
    print(f"  {CYAN}[{step:02d}/{total:02d}]{RESET} [{bar}] {description}")


def print_success(message: str) -> None:
    """Print a green success message."""
    print(f"  {GREEN}✓{RESET}  {message}")


def print_warning(message: str) -> None:
    """Print a yellow warning message."""
    print(f"  {YELLOW}⚠{RESET}  {message}")


def print_error(message: str) -> None:
    """Print a red error message."""
    print(f"  {RED}✗{RESET}  {message}")


def print_info(message: str) -> None:
    """Print a cyan informational message."""
    print(f"  {CYAN}ℹ{RESET}  {message}")


def get_system_info() -> dict:
    """
    Collect basic system information for inclusion in reports.

    Returns:
        dict: System info (OS, Python version, hostname, etc.)
    """
    return {
        "platform"      : platform.system(),
        "platform_ver"  : platform.version(),
        "architecture"  : platform.machine(),
        "python_version": platform.python_version(),
        "timestamp_utc" : datetime.now(timezone.utc).isoformat(),
        "pid"           : os.getpid(),
    }


def format_duration(seconds: float) -> str:
    """
    Format a duration in seconds as a human-readable string.

    Examples:
        45.3    → "45.3 s"
        123.7   → "2 min 3.7 s"
        3661.2  → "1 hr 1 min 1.2 s"

    Args:
        seconds : Duration in seconds.

    Returns:
        str: Formatted duration string.
    """
    if seconds < 60:
        return f"{seconds:.1f} s"
    elif seconds < 3600:
        m = int(seconds // 60)
        s = seconds % 60
        return f"{m} min {s:.1f} s"
    else:
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = seconds % 60
        return f"{h} hr {m} min {s:.1f} s"
