#!/usr/bin/env python3
"""
main.py
=======
Entry Point — 3D LiDAR-Based Shelter Damage Inspection System

This module orchestrates the complete autonomous inspection pipeline:

    Phase 1 : Robot Initialisation & Navigation
    Phase 2 : 3D LiDAR Scanning
    Phase 3 : Point Cloud Generation & Accumulation
    Phase 4 : 3D Environment Reconstruction
    Phase 5 : Structural Damage Detection
    Phase 6 : Severity Classification
    Phase 7 : Inspection Report Generation & Display

Run:
    python main.py [--shelter-id SH-001] [--robot-id TB3-01]
                   [--scans 8] [--no-plot] [--debug]

Author  : Team LiDAR-Inspect
Project : 3D LiDAR-Based Shelter Damage Inspection System
License : MIT
"""

import os
import sys
import time
import argparse
import logging

# ---------------------------------------------------------------------------
# Add the src directory to Python path so modules can import each other
# ---------------------------------------------------------------------------
_SRC_DIR = os.path.dirname(os.path.abspath(__file__))
if _SRC_DIR not in sys.path:
    sys.path.insert(0, _SRC_DIR)

# ---------------------------------------------------------------------------
# Project imports
# ---------------------------------------------------------------------------
from utils import (
    setup_logging, timer, timeit,
    print_banner, print_step, print_success, print_info,
    print_warning, get_system_info, format_duration,
    BOLD, CYAN, GREEN, RED, RESET,
)
from robot_controller   import RobotController
from lidar_processor    import LiDARProcessor
from pointcloud_generator import PointCloudGenerator
from environment_mapper import EnvironmentMapper
from damage_detector    import DamageDetector
from severity_classifier import SeverityClassifier
from report_generator   import ReportGenerator

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
TOTAL_STEPS     = 9     # Total pipeline phases for progress display
# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
TOTAL_STEPS     = 9     # Total pipeline phases for progress display
PROJECT_ROOT    = os.path.abspath(os.path.join(_SRC_DIR, "..", "..", ".."))
REPORTS_DIR     = os.path.join(PROJECT_ROOT, "reports")
LOG_FILE        = os.path.join(REPORTS_DIR, "inspection.log")
os.makedirs(REPORTS_DIR, exist_ok=True)


# ---------------------------------------------------------------------------
# Argument Parser
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    """
    Parse command-line arguments for the inspection pipeline.

    Returns:
        argparse.Namespace: Parsed arguments.
    """
    parser = argparse.ArgumentParser(
        prog        = "lidar_inspect",
        description = "3D LiDAR-Based Shelter Damage Inspection System",
        formatter_class = argparse.RawDescriptionHelpFormatter,
        epilog      = (
            "Examples:\n"
            "  python main.py\n"
            "  python main.py --shelter-id SH-042 --scans 12 --debug\n"
            "  python main.py --robot-id TB3-02 --no-plot\n"
        ),
    )
    parser.add_argument(
        "--shelter-id", "-s",
        type    = str,
        default = "SH-001",
        help    = "Unique identifier for the shelter being inspected (default: SH-001)",
    )
    parser.add_argument(
        "--robot-id", "-r",
        type    = str,
        default = "TB3-01",
        help    = "Robot identifier (default: TB3-01)",
    )
    parser.add_argument(
        "--scans", "-n",
        type    = int,
        default = 8,
        help    = "Number of LiDAR scan passes to perform (default: 8)",
    )
    parser.add_argument(
        "--no-plot",
        action  = "store_true",
        default = False,
        help    = "Skip interactive Matplotlib visualisation windows",
    )
    parser.add_argument(
        "--debug",
        action  = "store_true",
        default = False,
        help    = "Enable DEBUG-level logging for all modules",
    )
    parser.add_argument(
        "--output", "-o",
        type    = str,
        default = None,
        help    = "Override report output file path",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Pipeline Phases
# ---------------------------------------------------------------------------

def phase_1_init_robot(robot_id: str) -> RobotController:
    """
    Phase 1: Initialise the robot controller and verify subsystems.

    Args:
        robot_id : Robot identifier string.

    Returns:
        RobotController: Initialised controller object.
    """
    logger = logging.getLogger(__name__)
    print_step(1, TOTAL_STEPS, "Initialising Robot Controller …")

    controller = RobotController(
        robot_id      = robot_id,
        linear_speed  = 0.20,
        angular_speed = 0.50,
    )
    success = controller.initialize()

    if not success:
        logger.error("Robot initialisation failed!")
        sys.exit(1)

    print_success(f"Robot {robot_id} initialised | pose: {controller.pose}")
    return controller


def phase_2_navigate(controller: RobotController) -> None:
    """
    Phase 2: Launch autonomous navigation through the shelter.

    The robot executes a boustrophedon (lawnmower) sweep pattern to ensure
    complete coverage of the shelter floor area.

    Args:
        controller : Initialised RobotController.
    """
    logger = logging.getLogger(__name__)
    print_step(2, TOTAL_STEPS, "Launching Autonomous Navigation …")

    with timer("navigation"):
        scan_positions = controller.navigate()

    status = controller.get_status()
    print_success(
        f"Navigation complete | waypoints={len(scan_positions)} | "
        f"distance={status['distance_m']} m | battery={status['battery_pct']}%"
    )


def phase_3_lidar_scan(
    controller  : RobotController,
    lidar       : LiDARProcessor,
    num_scans   : int,
) -> list:
    """
    Phase 3: Capture 3D LiDAR scans at each navigation waypoint.

    The robot performs a 360° multi-layer scan at each of the recorded
    scan positions, building up dense coverage of the shelter volume.

    Args:
        controller : RobotController with recorded scan_positions.
        lidar      : Initialised LiDARProcessor.
        num_scans  : Number of scan passes to perform.

    Returns:
        list: Captured and filtered MultiLayerScan objects.
    """
    logger = logging.getLogger(__name__)
    print_step(3, TOTAL_STEPS, f"Performing 3D LiDAR Scans ({num_scans} passes) …")

    scans      = []
    positions  = controller.scan_positions or [(0.0, 0.0), (4.0, 3.0), (7.5, 5.5)]
    step       = max(1, len(positions) // num_scans)

    with timer("lidar scanning"):
        for i, (scan_pose) in enumerate(positions[::step][:num_scans]):
            rx = scan_pose.x if hasattr(scan_pose, 'x') else scan_pose[0]
            ry = scan_pose.y if hasattr(scan_pose, 'y') else scan_pose[1]
            rtheta = scan_pose.theta if hasattr(scan_pose, 'theta') else 0.0

            raw_scan      = lidar.generate_scan(rx, ry, rtheta)
            filtered_scan = lidar.filter_scan(raw_scan)
            scans.append(filtered_scan)

            stats = lidar.get_scan_statistics(filtered_scan)
            logger.debug(
                "Scan %d/%d | pts=%d | valid=%d | dropout=%.2f%%",
                i + 1, num_scans,
                stats["total_points"],
                stats["valid_points"],
                stats["dropout_rate"] * 100,
            )

    print_success(f"LiDAR scanning complete | {len(scans)} scans captured")
    return scans


def phase_4_generate_pointcloud(
    scans   : list,
    pcgen   : PointCloudGenerator,
    no_plot : bool,
) -> None:
    """
    Phase 4: Convert raw scans into 3D point clouds and accumulate.

    Each scan is converted from spherical coordinates (range, azimuth,
    elevation) to Cartesian (x, y, z) world-frame coordinates.

    Args:
        scans   : List of filtered MultiLayerScan objects.
        pcgen   : PointCloudGenerator instance.
        no_plot : If True, skip interactive popup.
    """
    logger = logging.getLogger(__name__)
    print_step(4, TOTAL_STEPS, "Generating 3D Point Cloud …")

    with timer("point cloud generation"):
        for scan in scans:
            cloud = pcgen.scan_to_pointcloud(scan)
            pcgen.accumulate(cloud)

    accumulated = pcgen.get_accumulated_cloud()
    downsampled = pcgen.downsample()

    print_success(
        f"Point cloud built | {accumulated.num_points:,} pts "
        f"→ {len(downsampled):,} pts (after voxel down-sampling)"
    )

    # Save point cloud visualization image automatically
    png_path = os.path.join(REPORTS_DIR, "point_cloud.png")
    try:
        pcgen.visualize_3d(
            title      = "3D Point Cloud — Damaged Shelter Reconstruction",
            save_path  = png_path,
            max_points = 20000,
        )
        print_success(f"Point cloud visualization saved → {png_path}")
    except Exception as exc:
        logger.warning("Point cloud plotting failed: %s", exc)


def phase_5_build_map(
    pcgen   : PointCloudGenerator,
    mapper  : EnvironmentMapper,
    no_plot : bool,
) -> None:
    """
    Phase 5: Reconstruct the 3D environment map from the accumulated cloud.

    Builds the occupancy grid, height map, and structural region
    classification from all accumulated LiDAR data.

    Args:
        pcgen   : PointCloudGenerator with accumulated cloud.
        mapper  : EnvironmentMapper instance.
        no_plot : If True, skip interactive plots.
    """
    logger = logging.getLogger(__name__)
    print_step(5, TOTAL_STEPS, "Building 3D Environment Map …")

    # Feed accumulated cloud into the mapper
    accumulated_cloud = pcgen.get_accumulated_cloud()
    mapper.accumulate_cloud(accumulated_cloud)

    with timer("environment mapping"):
        occ_grid   = mapper.build_occupancy_grid()
        regions    = mapper.classify_regions()
        height_map = mapper.compute_height_map()

    shelter_map = mapper.get_map()
    print_success(
        f"Map built | coverage={shelter_map.coverage_pct}% | "
        f"regions={len(regions)} | grid={occ_grid.width_cells}×{occ_grid.height_cells}"
    )
    for region in regions:
        logger.info("  Region: %-22s | pts=%d", region.label, len(region.points))

    # Save map visualization images automatically
    map_png_path = os.path.join(REPORTS_DIR, "environment_map.png")
    heatmap_png_path = os.path.join(REPORTS_DIR, "damage_heatmap.png")
    try:
        mapper.visualize_occupancy_grid(save_path=map_png_path)
        mapper.visualize_height_map(save_path=heatmap_png_path)
        print_success(f"Environment maps saved → {map_png_path}, {heatmap_png_path}")
    except Exception as exc:
        logger.warning("Map visualization failed: %s", exc)


def phase_6_detect_damage(mapper: EnvironmentMapper):
    """
    Phase 6: Run the structural damage detection pipeline.

    Args:
        mapper : EnvironmentMapper with a built shelter map.

    Returns:
        DamageReport: All detected damage instances.
    """
    logger = logging.getLogger(__name__)
    print_step(6, TOTAL_STEPS, "Detecting Structural Damage …")

    shelter_map = mapper.get_map()
    detector    = DamageDetector(shelter_map)

    with timer("damage detection"):
        damage_report = detector.detect()

    print_success(
        f"Damage detection complete | "
        f"{damage_report.damage_count} issues | "
        f"types: {damage_report.damage_types}"
    )
    return damage_report


def phase_7_classify_severity(
    damage_report,
    mapper: EnvironmentMapper,
):
    """
    Phase 7: Compute the structural severity score and risk level.

    Args:
        damage_report : DamageReport from DamageDetector.
        mapper        : EnvironmentMapper (provides coverage estimate).

    Returns:
        SeverityResult: Score, risk level, and recommendation.
    """
    logger = logging.getLogger(__name__)
    print_step(7, TOTAL_STEPS, "Classifying Damage Severity …")

    coverage    = mapper.get_map().coverage_pct
    classifier  = SeverityClassifier(damage_report, scan_coverage=coverage)

    with timer("severity classification"):
        severity = classifier.classify()

    print_success(
        f"Severity: score={severity.severity_score:.1f}/100 | "
        f"risk={severity.color_code}{BOLD}{severity.risk_level}{RESET}"
    )

    # Print score table to terminal
    print(f"\n{classifier.get_damage_table()}")
    print(f"{classifier.get_severity_summary(severity)}\n")

    return severity


def phase_8_generate_report(
    shelter_id    : str,
    robot_id      : str,
    controller    : RobotController,
    lidar         : LiDARProcessor,
    damage_report,
    severity,
    output_path   : str = None,
) -> str:
    """
    Phase 8: Assemble and save the formal inspection report.

    Args:
        shelter_id    : Shelter identifier.
        robot_id      : Robot identifier.
        controller    : RobotController (provides nav telemetry).
        lidar         : LiDARProcessor (provides scan stats).
        damage_report : DamageReport from DamageDetector.
        severity      : SeverityResult from SeverityClassifier.
        output_path   : Optional override for report file path.

    Returns:
        str: The full report content string.
    """
    logger = logging.getLogger(__name__)
    print_step(8, TOTAL_STEPS, "Generating Inspection Report …")

    # Gather telemetry
    robot_status = controller.get_status()
    nav_stats    = {
        "distance_m" : robot_status["distance_m"],
        "steps"      : robot_status["steps"],
        "battery_pct": robot_status["battery_pct"],
        "scans_taken": robot_status["scans_taken"],
    }

    # Gather scan stats from the most recent scan in history
    if lidar.scan_history:
        latest_scan = lidar.scan_history[-1]
        scan_stats  = lidar.get_scan_statistics(latest_scan)
        scan_stats["total_scans"] = len(lidar.scan_history)
    else:
        scan_stats = {"total_scans": 0}

    reporter = ReportGenerator(
        shelter_id    = shelter_id,
        robot_id      = robot_id,
        damage_report = damage_report,
        severity      = severity,
        scan_stats    = scan_stats,
        nav_stats     = nav_stats,
    )

    report_path = output_path or os.path.join(REPORTS_DIR, "inspection_report.txt")
    json_path   = os.path.join(REPORTS_DIR, "inspection_summary.json")

    with timer("report generation"):
        content = reporter.generate(output_path=report_path)
        reporter.generate_json_summary(output_path=json_path)

    print_success(f"Report saved → {report_path}")
    print_success(f"JSON Summary saved → {json_path}")
    return content


def phase_9_display_summary(
    controller   : RobotController,
    damage_report,
    severity,
    pcgen        : PointCloudGenerator,
    t_start      : float,
) -> None:
    """
    Phase 9: Print the final summary to the terminal.

    Args:
        controller    : RobotController for telemetry.
        damage_report : DamageReport.
        severity      : SeverityResult.
        pcgen         : PointCloudGenerator.
        t_start       : Pipeline start time (from time.perf_counter()).
    """
    elapsed       = time.perf_counter() - t_start
    robot_status  = controller.get_status()
    total_pts     = pcgen.get_accumulated_cloud().num_points

    print_step(9, TOTAL_STEPS, "Displaying Final Summary …")
    print()
    print_banner("INSPECTION COMPLETE — SUMMARY")

    rows = [
        ("Shelter ID",       severity.shelter_id),
        ("Robot ID",         robot_status["robot_id"]),
        ("Distance Covered", f"{robot_status['distance_m']} m"),
        ("LiDAR Scans",      str(robot_status["scans_taken"])),
        ("Battery Remaining",f"{robot_status['battery_pct']}%"),
        ("Damage Instances", str(damage_report.damage_count)),
        ("Severity Score",   f"{severity.severity_score:.1f} / 100"),
        ("Risk Level",
         f"{severity.color_code}{BOLD}{severity.risk_level}{RESET}"),
        ("Overall Confidence", f"{severity.confidence_overall:.1%}"),
        ("Pipeline Runtime",  format_duration(elapsed)),
    ]

    for label, value in rows:
        print(f"  {CYAN}{label:<25}{RESET}: {value}")

    # Formatted hackathon output block
    status_str = "SAFE FOR ENTRY" if severity.risk_level in ["SAFE", "LOW"] else "UNSAFE / RESTRICTED ENTRY"
    print("\n" + "=" * 40)
    print("3D LiDAR Shelter Inspection Complete")
    print("=" * 40)
    print("\nRobot Status:\n✓ Navigation Completed")
    print("\nLiDAR:\n✓ 360° Scan Complete")
    print(f"\nPoint Cloud:\n✓ Generated\n✓ Total Points: {total_pts:,}")
    print("\nEnvironment Map:\n✓ Created")
    print("\nDamage Detection:")
    for dt in damage_report.damage_types:
        print(f"✓ {dt}")
    print(f"\nSeverity:\n{severity.risk_level} ({severity.severity_score:.1f}/100)")
    print(f"\nInspection Status:\n{status_str}")
    print("\nInspection Report:\nSaved successfully")
    print(f"\nExecution Time:\n{elapsed:.2f} seconds")
    print("=" * 40 + "\n")

    print(f"  {GREEN}✔  Inspection pipeline completed successfully!{RESET}")
    print(f"  {CYAN}ℹ  Full outputs saved to: reports/{RESET}\n")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    """
    Top-level entry point that orchestrates the complete inspection pipeline.

    Parses arguments, sets up logging, and runs all 9 pipeline phases in
    sequence. Captures total runtime and displays a final summary.
    """
    args = parse_args()

    # ---- Setup logging ----
    log_level = logging.DEBUG if args.debug else logging.INFO
    setup_logging(
        level    = log_level,
        log_file = LOG_FILE,
    )
    logger = logging.getLogger(__name__)

    # ---- Banner ----
    print_banner("3D LiDAR-BASED SHELTER DAMAGE INSPECTION SYSTEM")
    sys_info = get_system_info()
    print_info(f"Python {sys_info['python_version']} | {sys_info['platform']}")
    print_info(f"Shelter: {args.shelter_id} | Robot: {args.robot_id}")
    print_info(f"Scan passes: {args.scans} | Plot: {not args.no_plot}")
    print()

    t_start = time.perf_counter()

    try:
        # ── Phase 1: Robot Initialisation ──────────────────────────────
        controller = phase_1_init_robot(args.robot_id)

        # ── Phase 2: Navigation ────────────────────────────────────────
        phase_2_navigate(controller)

        # ── Phase 3: LiDAR Scanning ────────────────────────────────────
        lidar = LiDARProcessor(enable_noise=True)
        scans = phase_3_lidar_scan(controller, lidar, args.scans)

        # ── Phase 4: Point Cloud Generation ───────────────────────────
        pcgen = PointCloudGenerator()
        phase_4_generate_pointcloud(scans, pcgen, args.no_plot)

        # ── Phase 5: Environment Mapping ───────────────────────────────
        mapper = EnvironmentMapper(shelter_id=args.shelter_id)
        phase_5_build_map(pcgen, mapper, args.no_plot)

        # ── Phase 6: Damage Detection ──────────────────────────────────
        damage_report = phase_6_detect_damage(mapper)

        # ── Phase 7: Severity Classification ──────────────────────────
        severity = phase_7_classify_severity(damage_report, mapper)

        # ── Phase 8: Report Generation ─────────────────────────────────
        phase_8_generate_report(
            shelter_id    = args.shelter_id,
            robot_id      = args.robot_id,
            controller    = controller,
            lidar         = lidar,
            damage_report = damage_report,
            severity      = severity,
            output_path   = args.output,
        )

        # ── Phase 9: Summary Display ───────────────────────────────────
        phase_9_display_summary(controller, damage_report, severity, pcgen, t_start)

        # Gracefully stop the robot
        controller.stop()

    except KeyboardInterrupt:
        print_warning("\nInspection interrupted by user (Ctrl+C).")
        try:
            controller.stop()
        except NameError:
            pass
        sys.exit(0)

    except Exception as exc:
        logger.exception("Unexpected error in inspection pipeline: %s", exc)
        sys.exit(1)


# ---------------------------------------------------------------------------
# Entry Guard
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    main()
