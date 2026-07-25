#!/usr/bin/env python3
"""
severity_classifier.py
=======================
Structural Damage Severity Classification module.

This module takes the damage detection results and computes a composite
severity score (0–100) using a weighted multi-factor model. The score is
then mapped to a categorical risk level following guidelines from:
    • FEMA P-154 Rapid Visual Screening of Buildings
    • ATC-20 Post-Earthquake Safety Evaluation of Buildings
    • UNHCR Shelter Assessment Framework

Scoring Factors:
    1. Damage type weight   — different failure modes have different safety impact.
    2. Damage extent        — larger damaged areas score higher.
    3. Detection confidence — uncertain detections are penalised.
    4. Damage count         — multiple independent damage types compound risk.
    5. Coverage penalty     — incomplete scan data inflates uncertainty.

Risk Levels:
    SAFE     [0–15]   : No significant structural compromise.
    LOW      [16–35]  : Minor damage, safe for rescue personnel with precautions.
    MEDIUM   [36–55]  : Moderate damage. Use secondary entrance; limit time inside.
    HIGH     [56–75]  : Severe damage. Only structural engineers should enter.
    CRITICAL [76–100] : Imminent collapse risk. No entry. Evacuate surroundings.

Author  : Team LiDAR-Inspect
Project : 3D LiDAR-Based Shelter Damage Inspection System
License : MIT
"""

import logging
import math
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional

from damage_detector import DamageReport, DamageInstance

# ---------------------------------------------------------------------------
# Logger
# ---------------------------------------------------------------------------
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Base severity score contributed by each damage type (0–100 scale)
DAMAGE_TYPE_WEIGHTS: Dict[str, float] = {
    "Collapsed Section" : 30.0,
    "Missing Wall"      : 22.0,
    "Broken Roof"       : 20.0,
    "Large Hole / Void" : 14.0,
    "Leaning Wall"      : 18.0,
}

# Risk level definitions: (label, min_score, max_score, colour_code, recommendation)
RISK_LEVELS: List[Tuple[str, int, int, str, str]] = [
    (
        "SAFE",
        0, 15,
        "\033[92m",   # Green
        "No immediate action required. Shelter is stable for rescue operations. "
        "Continue monitoring for aftershocks or secondary hazards.",
    ),
    (
        "LOW",
        16, 35,
        "\033[93m",   # Yellow
        "Minor structural damage detected. Rescue personnel may enter with hard "
        "hats and safety vests. Avoid damaged zones. Reassess within 6 hours.",
    ),
    (
        "MEDIUM",
        36, 55,
        "\033[33m",   # Orange (approx)
        "Moderate structural compromise. Use secondary entrance points. Limit "
        "occupancy to 2 people at a time. Structural engineer assessment recommended "
        "within 24 hours. Do not operate heavy machinery inside.",
    ),
    (
        "HIGH",
        56, 75,
        "\033[91m",   # Red
        "Severe structural damage. High probability of partial collapse within "
        "24–72 hours. Only qualified structural engineers should enter with full "
        "PPE. Establish 20 m exclusion zone around compromised sections. "
        "Emergency shoring required before any rescue operations.",
    ),
    (
        "CRITICAL",
        76, 100,
        "\033[31m",   # Dark Red
        "IMMINENT COLLAPSE RISK. Do NOT enter under any circumstances. Evacuate "
        "all personnel within 50 m radius immediately. Notify civil defence and "
        "structural emergency teams. Deploy remote drone for further assessment. "
        "Structure must be demolished / shored before any human entry.",
    ),
]

RESET_COLOR = "\033[0m"


# ---------------------------------------------------------------------------
# Data Classes
# ---------------------------------------------------------------------------

@dataclass
class SeverityResult:
    """
    Complete severity assessment result for a shelter inspection.

    Attributes:
        shelter_id         : Identifier of the inspected shelter.
        severity_score     : Numerical score in [0, 100].
        risk_level         : Categorical label (SAFE / LOW / MEDIUM / HIGH / CRITICAL).
        recommendation     : Actionable text recommendation for field teams.
        factor_breakdown   : Per-factor score contributions for audit traceability.
        confidence_overall : Weighted average confidence across all damage detections.
        color_code         : ANSI colour code for terminal display.
    """
    shelter_id        : str
    severity_score    : float
    risk_level        : str
    recommendation    : str
    factor_breakdown  : Dict[str, float] = field(default_factory=dict)
    confidence_overall: float = 0.0
    color_code        : str   = "\033[92m"

    def __repr__(self) -> str:
        return (
            f"SeverityResult(shelter={self.shelter_id}, "
            f"score={self.severity_score:.1f}, "
            f"risk={self.risk_level})"
        )


# ---------------------------------------------------------------------------
# SeverityClassifier
# ---------------------------------------------------------------------------

class SeverityClassifier:
    """
    Computes a composite structural damage severity score from detection results.

    The classifier implements a transparent, rule-based scoring model that is
    fully auditable and traceable — important for emergency management decisions
    where algorithmic accountability is required.

    Scoring Model (additive, capped at 100):
        1. Type Score     : Sum of damage-type weights for each unique damage type.
        2. Extent Penalty : Additional score for large-area damage (log scale).
        3. Count Penalty  : Multiplicative factor for multiple concurrent damage types.
        4. Confidence Adj : Down-weight score for low-confidence detections.
        5. Coverage Pct   : Additional uncertainty for low scan coverage.

    Attributes:
        damage_report : Input DamageReport from DamageDetector.
        scan_coverage : Estimated scan coverage percentage [0–100].
    """

    def __init__(
        self,
        damage_report: DamageReport,
        scan_coverage: float = 85.0,
    ) -> None:
        """
        Initialise the classifier.

        Args:
            damage_report : DamageReport from DamageDetector.detect().
            scan_coverage : Estimated percentage of shelter volume scanned (0–100).
        """
        self.damage_report = damage_report
        self.scan_coverage = max(0.0, min(100.0, scan_coverage))

        logger.info(
            "SeverityClassifier initialised | shelter=%s | %d damage(s) | coverage=%.1f%%",
            damage_report.shelter_id,
            damage_report.damage_count,
            scan_coverage,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def classify(self) -> SeverityResult:
        """
        Execute the full scoring pipeline and return a SeverityResult.

        Returns:
            SeverityResult: Complete severity assessment with score and risk level.
        """
        logger.info("Computing severity score …")

        score, breakdown = self._compute_score()

        # Determine risk level category
        risk_label, color, recommendation = self._map_score_to_risk(score)

        # Overall confidence (weighted mean)
        conf = self._compute_overall_confidence()

        result = SeverityResult(
            shelter_id         = self.damage_report.shelter_id,
            severity_score     = round(score, 2),
            risk_level         = risk_label,
            recommendation     = recommendation,
            factor_breakdown   = {k: round(v, 2) for k, v in breakdown.items()},
            confidence_overall = round(conf, 3),
            color_code         = color,
        )

        logger.info(
            "Severity Assessment → Score=%.1f | Risk=%s | Confidence=%.0f%%",
            result.severity_score, result.risk_level, result.confidence_overall * 100,
        )
        return result

    def get_severity_summary(self, result: SeverityResult) -> str:
        """
        Format a concise terminal-printable severity summary block.

        Args:
            result : A SeverityResult from classify().

        Returns:
            str: Multi-line formatted summary string.
        """
        bar_filled = int(result.severity_score / 5)
        bar_empty  = 20 - bar_filled
        bar        = "█" * bar_filled + "░" * bar_empty

        lines = [
            "",
            "┌─────────────────────────────────────────────┐",
            f"│  STRUCTURAL DAMAGE SEVERITY ASSESSMENT        │",
            f"│  Shelter: {result.shelter_id:<34} │",
            f"│  Score  : {result.severity_score:>5.1f} / 100                          │",
            f"│  Risk   : {result.color_code}{result.risk_level:<10}{RESET_COLOR}                           │",
            f"│  [{bar}]  {result.severity_score:5.1f}%  │",
            f"│  Confidence : {result.confidence_overall:>5.1%}                         │",
            f"│  Coverage   : {self.scan_coverage:>5.1f}%                         │",
            "├─────────────────────────────────────────────┤",
            "│  SCORE BREAKDOWN                             │",
        ]
        for factor, val in result.factor_breakdown.items():
            lines.append(f"│    {factor:<28} : {val:>5.1f}  │")

        lines += [
            "├─────────────────────────────────────────────┤",
            "│  RECOMMENDATION                              │",
        ]
        # Word-wrap recommendation to 44 chars
        words = result.recommendation.split()
        line  = "│  "
        for word in words:
            if len(line) + len(word) + 1 > 46:
                lines.append(f"{line:<46}│")
                line = "│    " + word + " "
            else:
                line += word + " "
        lines.append(f"{line:<46}│")
        lines.append("└─────────────────────────────────────────────┘")

        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Private Scoring Pipeline
    # ------------------------------------------------------------------

    def _compute_score(self) -> Tuple[float, Dict[str, float]]:
        """
        Execute the multi-factor scoring model.

        Returns:
            Tuple of (final_score, factor_breakdown_dict)
        """
        breakdown: Dict[str, float] = {}

        # ---- Factor 1: Damage Type Score ----
        unique_types = list({d.damage_type for d in self.damage_report.damage_instances})
        type_score   = sum(
            DAMAGE_TYPE_WEIGHTS.get(dt, 10.0) for dt in unique_types
        )
        breakdown["Type Score"] = min(type_score, 60.0)

        # ---- Factor 2: Extent Penalty ----
        total_extent = sum(d.extent_m for d in self.damage_report.damage_instances)
        extent_score = min(15.0, math.log1p(total_extent) * 5.0)
        breakdown["Extent Penalty"] = extent_score

        # ---- Factor 3: Damage Count Multiplier ----
        n = self.damage_report.damage_count
        count_score = min(10.0, (n - 1) * 2.5) if n > 1 else 0.0
        breakdown["Count Penalty"] = count_score

        # ---- Factor 4: Coverage Uncertainty ----
        # Low scan coverage → more undetected damage → higher uncertainty bonus
        gap_pct      = max(0.0, 100.0 - self.scan_coverage)
        cov_penalty  = min(10.0, gap_pct * 0.15)
        breakdown["Coverage Uncertainty"] = cov_penalty

        # ---- Factor 5: Confidence Adjustment ----
        # High confidence = trust the score; low confidence = add uncertainty
        avg_conf  = self._compute_overall_confidence()
        conf_adj  = min(5.0, (1.0 - avg_conf) * 10.0)
        breakdown["Confidence Adjustment"] = conf_adj

        # Raw score
        raw_score = (
            breakdown["Type Score"]
            + breakdown["Extent Penalty"]
            + breakdown["Count Penalty"]
            + breakdown["Coverage Uncertainty"]
            + breakdown["Confidence Adjustment"]
        )

        final_score = max(0.0, min(100.0, raw_score))
        breakdown["Total Score"] = round(final_score, 2)

        return final_score, breakdown

    def _map_score_to_risk(
        self, score: float
    ) -> Tuple[str, str, str]:
        """
        Map a numerical score to a categorical risk level.

        Args:
            score : Severity score in [0, 100].

        Returns:
            Tuple of (risk_label, ansi_color, recommendation_text)
        """
        for label, lo, hi, color, recommendation in RISK_LEVELS:
            if lo <= score <= hi:
                return label, color, recommendation

        # Default to CRITICAL for out-of-range (safety-first)
        last = RISK_LEVELS[-1]
        return last[0], last[3], last[4]

    def _compute_overall_confidence(self) -> float:
        """
        Compute the weighted average confidence across all damage instances.

        Returns:
            float: Overall confidence [0.0–1.0].
        """
        instances = self.damage_report.damage_instances
        if not instances:
            return 0.0

        total_weight = 0.0
        weighted_sum = 0.0
        for dmg in instances:
            weight        = DAMAGE_TYPE_WEIGHTS.get(dmg.damage_type, 5.0)
            weighted_sum += dmg.confidence * weight
            total_weight += weight

        return weighted_sum / total_weight if total_weight > 0 else 0.0

    # ------------------------------------------------------------------
    # Reporting Helpers
    # ------------------------------------------------------------------

    def get_damage_table(self) -> str:
        """
        Format a tabular summary of all damage instances for inclusion in reports.

        Returns:
            str: ASCII table of detected damage with coordinates and scores.
        """
        if not self.damage_report.damage_instances:
            return "  No structural damage detected.\n"

        header  = f"  {'#':<4} {'Type':<22} {'X (m)':<8} {'Y (m)':<8} {'Z (m)':<8} {'Extent':<8} {'Conf.':<8}\n"
        divider = "  " + "─" * 72 + "\n"
        rows    = ""

        for i, dmg in enumerate(self.damage_report.damage_instances, start=1):
            x, y, z = dmg.location_xyz
            rows += (
                f"  {i:<4} {dmg.damage_type:<22} "
                f"{x:<8.2f} {y:<8.2f} {z:<8.2f} "
                f"{dmg.extent_m:<8.2f} {dmg.confidence:<8.0%}\n"
            )

        return header + divider + rows + divider
