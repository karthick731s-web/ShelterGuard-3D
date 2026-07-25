#!/usr/bin/env python3
"""
report_generator.py
====================
Professional Inspection Report Generator for the Shelter Inspection System.

This module takes the processed inspection results — damage detections,
severity scores, robot telemetry, and scan statistics — and assembles
them into a structured, professional-grade inspection report.

The report format follows conventions from structural engineering field
reports and civil defence damage assessment forms, making it suitable for
presentation to emergency management authorities.

Output formats:
    • Plain-text  (.txt)  : Terminal-printable, universally compatible.
    • Console dump        : Rich terminal output with ANSI colour codes.

In a real deployment, additional formats could include:
    • PDF via reportlab / WeasyPrint
    • JSON API payload for integration with disaster management platforms
    • KML file for georeferenced GIS damage overlays

Author  : Team LiDAR-Inspect
Project : 3D LiDAR-Based Shelter Damage Inspection System
License : MIT
"""

import os
import logging
from datetime import datetime, timezone
from typing import Optional

from damage_detector import DamageReport
from severity_classifier import SeverityResult

# ---------------------------------------------------------------------------
# Logger
# ---------------------------------------------------------------------------
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
REPORT_DIR          = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))
    ))),
    "reports",
)
DEFAULT_REPORT_NAME = "inspection_report.txt"
RESET               = "\033[0m"
BOLD                = "\033[1m"
CYAN                = "\033[96m"
GREEN               = "\033[92m"
YELLOW              = "\033[93m"
RED                 = "\033[91m"
DIM                 = "\033[2m"


# ---------------------------------------------------------------------------
# ReportGenerator
# ---------------------------------------------------------------------------

class ReportGenerator:
    """
    Assembles and persists a professional structural inspection report.

    The report is structured in clearly labelled sections:
        1. Cover / Header
        2. Mission Overview
        3. Robot & Sensor Details
        4. Scan Statistics
        5. Damage Inventory
        6. Severity Assessment
        7. Recommendations
        8. Appendix: Raw Damage Data

    Attributes:
        shelter_id   : Unique shelter identifier.
        robot_id     : Robot that performed the inspection.
        damage_report: DamageReport from DamageDetector.
        severity     : SeverityResult from SeverityClassifier.
        scan_stats   : Dictionary of scan quality metrics.
        nav_stats    : Dictionary of navigation telemetry.
        report_path  : Full filesystem path where the TXT report is saved.
    """

    def __init__(
        self,
        shelter_id   : str,
        robot_id     : str,
        damage_report: DamageReport,
        severity     : SeverityResult,
        scan_stats   : Optional[dict] = None,
        nav_stats    : Optional[dict] = None,
    ) -> None:
        """
        Initialise the report generator with all inspection results.

        Args:
            shelter_id    : Unique shelter identifier string.
            robot_id      : Robot identifier string.
            damage_report : DamageReport from DamageDetector.detect().
            severity      : SeverityResult from SeverityClassifier.classify().
            scan_stats    : Optional dict with LiDAR scan quality metrics.
            nav_stats     : Optional dict with robot navigation telemetry.
        """
        self.shelter_id    = shelter_id
        self.robot_id      = robot_id
        self.damage_report = damage_report
        self.severity      = severity
        self.scan_stats    = scan_stats or {}
        self.nav_stats     = nav_stats  or {}
        self.report_path   = os.path.join(REPORT_DIR, DEFAULT_REPORT_NAME)

        # Inspection timestamp
        self.timestamp     = datetime.now(timezone.utc)
        self.timestamp_str = self.timestamp.strftime("%Y-%m-%d %H:%M:%S UTC")

        logger.info(
            "ReportGenerator initialised | shelter=%s | robot=%s | timestamp=%s",
            shelter_id, robot_id, self.timestamp_str,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate(self, output_path: Optional[str] = None) -> str:
        """
        Generate the full inspection report and save it to disk.

        Args:
            output_path : Override the default report file path.

        Returns:
            str: The complete report content as a string.
        """
        if output_path:
            self.report_path = output_path

        # Ensure the output directory exists
        os.makedirs(os.path.dirname(self.report_path), exist_ok=True)

        content = self._build_report()

        # Write plain-text report (strip ANSI codes)
        plain_text = self._strip_ansi(content)
        try:
            with open(self.report_path, "w", encoding="utf-8") as fh:
                fh.write(plain_text)
            logger.info("Report saved → %s", self.report_path)
        except OSError as exc:
            logger.error("Failed to save report: %s", exc)

        return content   # Return ANSI-coloured version for terminal display

    def display(self, content: Optional[str] = None) -> None:
        """
        Print the inspection report to stdout with ANSI colour formatting.

        Args:
            content : Pre-generated report string (calls generate() if None).
        """
        if content is None:
            content = self._build_report()
        print(content)

    # ------------------------------------------------------------------
    # Report Construction
    # ------------------------------------------------------------------

    def _build_report(self) -> str:
        """
        Assemble the full report by concatenating all section builders.

        Returns:
            str: Complete, formatted report with ANSI colour codes.
        """
        sections = [
            self._section_header(),
            self._section_mission_overview(),
            self._section_robot_details(),
            self._section_scan_statistics(),
            self._section_damage_inventory(),
            self._section_severity_assessment(),
            self._section_recommendations(),
            self._section_appendix(),
            self._section_footer(),
        ]
        return "\n".join(sections)

    def _section_header(self) -> str:
        """Generate the report cover / header section."""
        return (
            f"\n{BOLD}{CYAN}"
            "╔══════════════════════════════════════════════════════════════════╗\n"
            "║   3D LiDAR-BASED SHELTER DAMAGE INSPECTION SYSTEM               ║\n"
            "║   AUTONOMOUS STRUCTURAL INSPECTION REPORT                        ║\n"
            "║   ─────────────────────────────────────────────────────────────  ║\n"
            f"║   Report #    : RPT-{self.shelter_id}-{self.timestamp.strftime('%Y%m%d%H%M')}               ║\n"
            f"║   Shelter ID  : {self.shelter_id:<52}║\n"
            f"║   Robot ID    : {self.robot_id:<52}║\n"
            f"║   Timestamp   : {self.timestamp_str:<52}║\n"
            f"║   System      : TurtleBot3 + Velodyne VLP-16 LiDAR             ║\n"
            "╚══════════════════════════════════════════════════════════════════╝"
            f"{RESET}\n"
        )

    def _section_mission_overview(self) -> str:
        """Generate the mission overview section."""
        return (
            f"\n{BOLD}━━━  1. MISSION OVERVIEW  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{RESET}\n"
            "\n"
            "  Mission Type   : Post-Disaster Shelter Structural Inspection\n"
            "  Inspection Mode: Fully Autonomous (No Manual Teleoperation)\n"
            f"  Shelter ID     : {self.shelter_id}\n"
            f"  Inspection Date: {self.timestamp.strftime('%B %d, %Y')}\n"
            f"  Inspection Time: {self.timestamp.strftime('%H:%M:%S UTC')}\n"
            f"  Scan Coverage  : {self.severity.confidence_overall * 100:.1f}% (estimated)\n"
            "\n"
            "  BACKGROUND:\n"
            "  Following a major seismic/flood event, this shelter was flagged for\n"
            "  autonomous robotic inspection due to safety concerns preventing manual\n"
            "  entry. A TurtleBot3 equipped with a Velodyne VLP-16 3D LiDAR sensor\n"
            "  was deployed to perform a complete structural damage assessment.\n"
        )

    def _section_robot_details(self) -> str:
        """Generate the robot platform and sensor details section."""
        nav = self.nav_stats
        return (
            f"\n{BOLD}━━━  2. ROBOT & SENSOR SPECIFICATIONS  ━━━━━━━━━━━━━━━━━━━━━━━━━{RESET}\n"
            "\n"
            "  ┌─── Robot Platform ──────────────────────────────────────────┐\n"
            f"  │  Robot ID           : {self.robot_id:<38}│\n"
            "  │  Platform           : TurtleBot3 Burger (ROBOTIS)           │\n"
            "  │  Locomotion         : Differential Drive, 2×DYNAMIXEL XL430 │\n"
            "  │  Max Speed          : 0.22 m/s linear | 2.84 rad/s angular  │\n"
            "  │  On-Board Computer  : Raspberry Pi 4B (4 GB RAM)            │\n"
            "  │  OS                 : Ubuntu 22.04 LTS + ROS2 Humble        │\n"
            f"  │  Total Distance     : {str(nav.get('distance_m', 'N/A')):<38}│\n"
            f"  │  Steps / Waypoints  : {str(nav.get('steps', 'N/A')):<38}│\n"
            f"  │  Battery Remaining  : {str(nav.get('battery_pct', 'N/A')) + '%':<38}│\n"
            "  └─────────────────────────────────────────────────────────────┘\n"
            "\n"
            "  ┌─── LiDAR Sensor ────────────────────────────────────────────┐\n"
            "  │  Model              : Velodyne VLP-16 (Puck)                │\n"
            "  │  Channels           : 16 vertical layers                    │\n"
            "  │  Horizontal FOV     : 360°                                  │\n"
            "  │  Vertical FOV       : -15° to +15°                          │\n"
            "  │  Max Range          : 100 m (10 m used indoor)              │\n"
            "  │  Range Accuracy     : ±3 cm                                 │\n"
            "  │  Rotation Rate      : 10 Hz (300,000 points/sec)            │\n"
            "  │  ROS2 Topic         : /velodyne_points (PointCloud2)        │\n"
            "  └─────────────────────────────────────────────────────────────┘\n"
        )

    def _section_scan_statistics(self) -> str:
        """Generate the LiDAR scan quality statistics section."""
        s = self.scan_stats
        return (
            f"\n{BOLD}━━━  3. SCAN QUALITY STATISTICS  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{RESET}\n"
            "\n"
            f"  Total Scans Captured  : {s.get('total_scans', 'N/A')}\n"
            f"  Total Points          : {s.get('total_points', 'N/A'):,} pts\n"
            f"  Valid Points          : {s.get('valid_points', 'N/A'):,} pts\n"
            f"  Signal Dropout Rate   : {s.get('dropout_rate', 0.0):.2%}\n"
            f"  Range (Min / Max)     : {s.get('range_min_m', 'N/A')} m  /  {s.get('range_max_m', 'N/A')} m\n"
            f"  Mean Range            : {s.get('range_mean_m', 'N/A')} m\n"
            f"  Range Std Deviation   : {s.get('range_std_m', 'N/A')} m\n"
            f"  Scan Coverage         : {self.severity.confidence_overall * 100:.1f}%\n"
            f"  Noise Filtering       : Statistical Outlier Removal (±3σ, 5-ray window)\n"
            f"  Registration          : Odometry-based (ICP in full deployment)\n"
        )

    def _section_damage_inventory(self) -> str:
        """Generate the full damage inventory section."""
        dr = self.damage_report

        header = (
            f"\n{BOLD}━━━  4. DAMAGE INVENTORY  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{RESET}\n"
            f"\n"
            f"  Total Damage Instances  : {dr.damage_count}\n"
            f"  Unique Damage Types     : {len(dr.damage_types)}\n"
            f"  Estimated Damage Area   : {dr.total_damage_area:.2f} m²\n"
            f"  Detection Time          : {dr.detection_time_s:.4f} s\n"
            f"\n"
            f"  Damage Types Detected:\n"
        )
        for dt in dr.damage_types:
            header += f"    ✦ {dt}\n"

        # Tabulated damage list
        header += (
            f"\n  {'──'*36}\n"
            f"  {'#':<4} {'Type':<22} {'X':>6} {'Y':>6} {'Z':>6}  "
            f"{'Extent':>7}  {'Conf.':>6}\n"
            f"  {'──'*36}\n"
        )

        for i, dmg in enumerate(dr.damage_instances, 1):
            x, y, z = dmg.location_xyz
            header += (
                f"  {i:<4} {dmg.damage_type:<22} "
                f"{x:>6.2f} {y:>6.2f} {z:>6.2f}  "
                f"{dmg.extent_m:>6.2f}m  "
                f"{dmg.confidence:>6.0%}\n"
            )

        header += f"  {'──'*36}\n"
        return header

    def _section_severity_assessment(self) -> str:
        """Generate the severity score and risk assessment section."""
        sv = self.severity
        bar_fill  = int(sv.severity_score / 5)
        bar_empty = 20 - bar_fill
        bar       = "█" * bar_fill + "░" * bar_empty

        return (
            f"\n{BOLD}━━━  5. SEVERITY ASSESSMENT  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{RESET}\n"
            f"\n"
            f"  Severity Score   : {sv.severity_score:.1f} / 100\n"
            f"  Risk Level       : {sv.color_code}{BOLD}{sv.risk_level}{RESET}\n"
            f"  Score Bar        : [{bar}]  {sv.severity_score:.1f}%\n"
            f"  Overall Confidence: {sv.confidence_overall:.1%}\n"
            f"\n"
            f"  Score Factor Breakdown:\n"
        ) + "\n".join(
            f"    {k:<30}: {v:>6.2f} pts"
            for k, v in sv.factor_breakdown.items()
        ) + "\n"

    def _section_recommendations(self) -> str:
        """Generate the operational recommendations section."""
        sv = self.severity
        return (
            f"\n{BOLD}━━━  6. RECOMMENDATIONS  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{RESET}\n"
            f"\n"
            f"  {sv.color_code}{BOLD}[{sv.risk_level}]{RESET} {sv.recommendation}\n"
            f"\n"
            "  General Guidance:\n"
            "  ● All rescue personnel to review damage map before entry.\n"
            "  ● Maintain radio contact with outside team at all times.\n"
            "  ● Place structural monitors (crack gauges) on damaged walls.\n"
            "  ● Re-inspect after every 4 hours or any aftershock event.\n"
            "  ● This report does NOT replace assessment by a licensed\n"
            "    structural engineer — it is an initial triage tool only.\n"
        )

    def _section_appendix(self) -> str:
        """Generate the appendix with full raw damage descriptions."""
        lines = [
            f"\n{BOLD}━━━  APPENDIX A: DETAILED DAMAGE DESCRIPTIONS  ━━━━━━━━━━━━━━━━━{RESET}\n"
        ]
        for i, dmg in enumerate(self.damage_report.damage_instances, 1):
            x, y, z = dmg.location_xyz
            lines += [
                f"\n  [{i}] {dmg.damage_type.upper()}",
                f"      Location   : ({x:.3f}, {y:.3f}, {z:.3f}) m",
                f"      Extent     : {dmg.extent_m:.3f} m",
                f"      Confidence : {dmg.confidence:.1%}",
                f"      Description: {dmg.description}",
            ]
            if dmg.evidence_pts:
                lines.append("      Evidence Points (sample):")
                for ep in dmg.evidence_pts[:3]:
                    lines.append(f"        → ({ep[0]:.2f}, {ep[1]:.2f}, {ep[2]:.2f})")

        return "\n".join(lines) + "\n"

    def _section_footer(self) -> str:
        """Generate the report footer with legal disclaimer."""
        return (
            f"\n{DIM}"
            "════════════════════════════════════════════════════════════════════\n"
            "  DISCLAIMER: This report was generated by an autonomous robotic\n"
            "  inspection system. The results are based on LiDAR sensor data\n"
            "  and algorithmic analysis. All findings must be verified by a\n"
            "  qualified structural engineer before any decisions are made\n"
            "  regarding building occupancy, demolition, or repairs.\n"
            "\n"
            "  3D LiDAR-Based Shelter Damage Inspection System\n"
            f"  Generated: {self.timestamp_str}\n"
            "  © 2025 Team LiDAR-Inspect. Licensed under MIT.\n"
            "════════════════════════════════════════════════════════════════════"
            f"{RESET}\n"
        )

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------

    @staticmethod
    def _strip_ansi(text: str) -> str:
        """
        Remove ANSI terminal escape codes from a string.

        Used when writing the plain-text file to disk so that the saved
        report is cleanly readable in any text editor.

        Args:
            text : String possibly containing ANSI escape sequences.

        Returns:
            str: Clean text without any ANSI codes.
        """
        import re
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        return ansi_escape.sub('', text)

    def generate_json_summary(self, output_path: Optional[str] = None) -> dict:
        """
        Generate and save a structured JSON summary of the inspection results.

        Args:
            output_path: Optional path for the json file.

        Returns:
            dict: The JSON-serializable dictionary summary.
        """
        import json
        json_path = output_path or os.path.join(REPORT_DIR, "inspection_summary.json")
        os.makedirs(os.path.dirname(json_path), exist_ok=True)

        summary_data = {
            "shelter_id": self.shelter_id,
            "robot_id": self.robot_id,
            "timestamp": self.timestamp_str,
            "severity": {
                "score": self.severity.severity_score,
                "risk_level": self.severity.risk_level,
                "recommendation": self.severity.recommendation,
                "confidence_overall": self.severity.confidence_overall,
                "factor_breakdown": self.severity.factor_breakdown,
            },
            "damage_summary": {
                "total_count": self.damage_report.damage_count,
                "total_area_m2": round(self.damage_report.total_damage_area, 2),
                "damage_types": self.damage_report.damage_types,
                "instances": [
                    {
                        "type": d.damage_type,
                        "location_xyz": d.location_xyz,
                        "extent_m": d.extent_m,
                        "confidence": d.confidence,
                        "description": d.description,
                    }
                    for d in self.damage_report.damage_instances
                ],
            },
            "navigation_stats": self.nav_stats,
            "scan_stats": self.scan_stats,
        }

        try:
            with open(json_path, "w", encoding="utf-8") as fh:
                json.dump(summary_data, fh, indent=2)
            logger.info("JSON summary saved → %s", json_path)
        except OSError as exc:
            logger.error("Failed to save JSON summary: %s", exc)

        return summary_data

