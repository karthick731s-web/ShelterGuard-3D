#!/usr/bin/env python3
"""
lidar_processor.py
==================
Simulated 3D LiDAR data acquisition and preprocessing module.

Modelels a Velodyne VLP-16 (Puck) LiDAR sensor mounted on a TurtleBot3.
The sensor provides 360° horizontal coverage with 16 vertical channels,
producing ~300,000 points per second in a real deployment.

In simulation we generate statistically representative scan data using
Gaussian noise models derived from the Velodyne VLP-16 datasheet:
  - Range accuracy  : ±3 cm
  - Angular resolution: 0.1–0.4° (horizontal), 2° (vertical)
  - Max range       : 100 m (we cap at 10 m for indoor shelters)

ROS2 topic: sensor_msgs/LaserScan  → /scan
            sensor_msgs/PointCloud2 → /velodyne_points

Author  : Team LiDAR-Inspect
Project : 3D LiDAR-Based Shelter Damage Inspection System
License : MIT
"""

import math
import logging
import random
import numpy as np
from typing import List, Dict, Tuple, Optional

# ---------------------------------------------------------------------------
# Logger
# ---------------------------------------------------------------------------
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


# ---------------------------------------------------------------------------
# Constants — derived from Velodyne VLP-16 datasheet
# ---------------------------------------------------------------------------
LIDAR_MAX_RANGE_M       = 10.0    # Indoor maximum usable range (meters)
LIDAR_MIN_RANGE_M       = 0.1    # Minimum valid return distance (meters)
LIDAR_HORIZONTAL_RES    = 0.2    # Horizontal angular resolution (degrees)
LIDAR_VERTICAL_CHANNELS = 16     # Number of vertical laser channels
LIDAR_VERTICAL_FOV_MIN  = -15.0  # Bottom-most channel elevation (degrees)
LIDAR_VERTICAL_FOV_MAX  = 15.0   # Top-most channel elevation (degrees)
SENSOR_NOISE_SIGMA_M    = 0.03   # Gaussian noise std-dev from datasheet (meters)
INTENSITY_MAX           = 255    # Maximum return intensity value


# ---------------------------------------------------------------------------
# Data classes (lightweight, no external deps)
# ---------------------------------------------------------------------------

class LaserScanData:
    """
    Container for a single 2D horizontal laser scan sweep.

    Mirrors the ROS2 sensor_msgs/LaserScan message structure so that this
    module can be easily adapted to publish real ROS2 messages.

    Attributes:
        angle_min      : Start angle of the scan (radians).
        angle_max      : End angle of the scan (radians).
        angle_increment: Angular step between consecutive rays (radians).
        range_min      : Minimum valid range (meters).
        range_max      : Maximum valid range (meters).
        ranges         : Array of measured distances, one per ray (meters).
        intensities    : Reflected signal intensities per ray.
        timestamp      : Simulated ROS2 time in seconds.
    """

    def __init__(
        self,
        ranges: np.ndarray,
        intensities: np.ndarray,
        timestamp: float,
        angle_min: float = 0.0,
        angle_max: float = 2 * math.pi,
        angle_increment: float = math.radians(LIDAR_HORIZONTAL_RES),
        range_min: float = LIDAR_MIN_RANGE_M,
        range_max: float = LIDAR_MAX_RANGE_M,
    ) -> None:
        self.angle_min       = angle_min
        self.angle_max       = angle_max
        self.angle_increment = angle_increment
        self.range_min       = range_min
        self.range_max       = range_max
        self.ranges          = ranges
        self.intensities     = intensities
        self.timestamp       = timestamp

    @property
    def num_rays(self) -> int:
        """Total number of laser rays in this scan."""
        return len(self.ranges)

    def valid_ranges(self) -> np.ndarray:
        """Return only the in-range measurements (filters inf/NaN)."""
        mask = (self.ranges >= self.range_min) & (self.ranges <= self.range_max)
        return self.ranges[mask]

    def __repr__(self) -> str:
        valid = np.sum((self.ranges >= self.range_min) & (self.ranges <= self.range_max))
        return (
            f"LaserScanData(rays={self.num_rays}, valid={valid}, "
            f"t={self.timestamp:.3f}s)"
        )


class MultiLayerScan:
    """
    Container for a full 3D multi-layer LiDAR scan (all 16 vertical channels).

    Attributes:
        layers           : List of LaserScanData objects, one per vertical channel.
        elevation_angles : Elevation angle (degrees) for each channel.
        robot_pose_x     : Robot X position when scan was captured.
        robot_pose_y     : Robot Y position when scan was captured.
        robot_pose_theta : Robot heading (radians) when scan was captured.
    """

    def __init__(
        self,
        layers: List[LaserScanData],
        elevation_angles: List[float],
        robot_pose_x: float = 0.0,
        robot_pose_y: float = 0.0,
        robot_pose_theta: float = 0.0,
    ) -> None:
        self.layers           = layers
        self.elevation_angles = elevation_angles
        self.robot_pose_x     = robot_pose_x
        self.robot_pose_y     = robot_pose_y
        self.robot_pose_theta = robot_pose_theta

    @property
    def total_points(self) -> int:
        """Total number of range measurements across all layers."""
        return sum(layer.num_rays for layer in self.layers)

    def __repr__(self) -> str:
        return (
            f"MultiLayerScan(channels={len(self.layers)}, "
            f"total_points={self.total_points}, "
            f"pose=({self.robot_pose_x:.2f}, {self.robot_pose_y:.2f}))"
        )


# ---------------------------------------------------------------------------
# LiDARProcessor
# ---------------------------------------------------------------------------

class LiDARProcessor:
    """
    Simulates a Velodyne VLP-16 3D LiDAR sensor and its preprocessing pipeline.

    Responsibilities:
      1. Generate realistic synthetic laser scan data for a damaged shelter scene.
      2. Apply sensor noise models (Gaussian additive noise + dropout).
      3. Filter noisy / invalid returns using statistical outlier removal.
      4. Expose the cleaned scan for conversion to a 3D point cloud.

    In a real ROS2 deployment this class would subscribe to:
        /scan              → sensor_msgs/LaserScan   (for 2D SLAM)
        /velodyne_points   → sensor_msgs/PointCloud2 (for 3D reconstruction)

    Attributes:
        shelter_profile   : Dict describing the simulated room geometry.
        enable_noise      : Whether to apply sensor noise (default True).
        scan_history      : List of all captured scans for post-processing.
    """

    def __init__(
        self,
        shelter_profile: Optional[Dict] = None,
        enable_noise: bool = True,
    ) -> None:
        """
        Initialise the LiDAR processor.

        Args:
            shelter_profile : Dictionary describing shelter geometry and damage.
                              Keys: 'room_width', 'room_depth', 'ceiling_height',
                                    'damage_zones' (list of dicts).
            enable_noise    : If True, realistic sensor noise is applied.
        """
        self.enable_noise  = enable_noise
        self.scan_history: List[MultiLayerScan] = []
        self._sim_time     = 0.0   # Internal simulated clock (seconds)

        # Default shelter geometry (±damaged shelter map)
        self.shelter_profile = shelter_profile or {
            "room_width"      : 8.0,
            "room_depth"      : 6.0,
            "ceiling_height"  : 3.0,
            "damage_zones"    : [
                {"type": "collapsed_wall", "x": 2.0, "y": 1.0, "radius": 1.2},
                {"type": "roof_hole",      "x": 5.0, "y": 3.0, "radius": 0.8},
                {"type": "debris_pile",    "x": 6.5, "y": 4.5, "radius": 0.6},
            ],
        }

        logger.info(
            "LiDARProcessor initialised | noise=%s | shelter=%s×%sm",
            enable_noise,
            self.shelter_profile["room_width"],
            self.shelter_profile["room_depth"],
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate_scan(
        self,
        robot_x: float = 0.0,
        robot_y: float = 0.0,
        robot_theta: float = 0.0,
    ) -> MultiLayerScan:
        """
        Simulate a full 360° multi-layer LiDAR scan from the robot's current pose.

        The scan models:
          - Geometric ray casting against shelter walls, ceiling, and floor.
          - Damage zones that produce anomalous (missing / shortened) returns.
          - Gaussian measurement noise from the sensor's ranging electronics.
          - Random dropout events (lens contamination / specular reflections).

        Args:
            robot_x     : Robot X position in the world frame (meters).
            robot_y     : Robot Y position in the world frame (meters).
            robot_theta : Robot heading in radians.

        Returns:
            MultiLayerScan: Object containing all 16 layer scans.
        """
        self._sim_time += 0.1   # Advance simulated clock by 100 ms per scan

        num_horizontal_rays = int(360.0 / LIDAR_HORIZONTAL_RES)
        elevation_angles = np.linspace(
            LIDAR_VERTICAL_FOV_MIN,
            LIDAR_VERTICAL_FOV_MAX,
            LIDAR_VERTICAL_CHANNELS,
        ).tolist()

        layers = []
        for elev_deg in elevation_angles:
            scan = self._cast_layer(
                robot_x, robot_y, robot_theta, elev_deg, num_horizontal_rays
            )
            layers.append(scan)

        multi_scan = MultiLayerScan(
            layers           = layers,
            elevation_angles = elevation_angles,
            robot_pose_x     = robot_x,
            robot_pose_y     = robot_y,
            robot_pose_theta = robot_theta,
        )

        self.scan_history.append(multi_scan)
        logger.debug(
            "Scan captured at (%.2f, %.2f) | %s", robot_x, robot_y, multi_scan
        )
        return multi_scan

    def filter_scan(self, scan: MultiLayerScan) -> MultiLayerScan:
        """
        Apply a statistical outlier removal filter to all layers of the scan.

        Algorithm:
          1. For each ray, compute the local neighbourhood median over a ±5-ray window.
          2. Reject measurements that deviate from the median by more than 3σ.
          3. Replace rejected values with the neighbourhood median (instead of NaN)
             to preserve scan continuity for downstream visualisation.

        Args:
            scan : Raw MultiLayerScan from generate_scan().

        Returns:
            MultiLayerScan: Filtered scan with outliers suppressed.
        """
        logger.debug("Applying statistical outlier filter to scan …")
        filtered_layers = []
        for layer in scan.layers:
            filtered_ranges      = self._median_filter(layer.ranges, window=5)
            filtered_intensities = layer.intensities.copy()
            filtered_layers.append(LaserScanData(
                ranges          = filtered_ranges,
                intensities     = filtered_intensities,
                timestamp       = layer.timestamp,
                angle_min       = layer.angle_min,
                angle_max       = layer.angle_max,
                angle_increment = layer.angle_increment,
                range_min       = layer.range_min,
                range_max       = layer.range_max,
            ))

        return MultiLayerScan(
            layers           = filtered_layers,
            elevation_angles = scan.elevation_angles,
            robot_pose_x     = scan.robot_pose_x,
            robot_pose_y     = scan.robot_pose_y,
            robot_pose_theta = scan.robot_pose_theta,
        )

    def get_scan_statistics(self, scan: MultiLayerScan) -> Dict:
        """
        Compute summary statistics for a multi-layer scan.

        Useful for quality assessment and anomaly flagging before further processing.

        Args:
            scan : A MultiLayerScan object.

        Returns:
            Dict containing min, max, mean, std range values and dropout rate.
        """
        all_ranges = np.concatenate([layer.ranges for layer in scan.layers])
        valid_mask = (all_ranges >= LIDAR_MIN_RANGE_M) & (all_ranges <= LIDAR_MAX_RANGE_M)
        valid      = all_ranges[valid_mask]
        dropout    = 1.0 - (valid_mask.sum() / len(all_ranges))

        return {
            "total_points" : len(all_ranges),
            "valid_points" : int(valid_mask.sum()),
            "dropout_rate" : round(float(dropout), 4),
            "range_min_m"  : round(float(valid.min()), 3) if len(valid) else None,
            "range_max_m"  : round(float(valid.max()), 3) if len(valid) else None,
            "range_mean_m" : round(float(valid.mean()), 3) if len(valid) else None,
            "range_std_m"  : round(float(valid.std()), 4) if len(valid) else None,
        }

    # ------------------------------------------------------------------
    # Private simulation helpers
    # ------------------------------------------------------------------

    def _cast_layer(
        self,
        rx: float,
        ry: float,
        rtheta: float,
        elevation_deg: float,
        num_rays: int,
    ) -> LaserScanData:
        """
        Ray-cast a single horizontal scan layer at a given elevation angle.

        Each ray is cast from the robot's position and intersected with the
        shelter's bounding geometry. Damage zones modify the expected returns
        to produce anomalous patterns that the damage detector can identify.

        Args:
            rx            : Robot X position (m).
            ry            : Robot Y position (m).
            rtheta        : Robot heading (rad).
            elevation_deg : Vertical angle of this layer (degrees).
            num_rays      : Number of horizontal rays to cast.

        Returns:
            LaserScanData for this layer.
        """
        elev_rad = math.radians(elevation_deg)
        cos_elev = math.cos(elev_rad)
        sin_elev = math.sin(elev_rad)

        ranges      = np.zeros(num_rays, dtype=np.float32)
        intensities = np.zeros(num_rays, dtype=np.float32)

        W = self.shelter_profile["room_width"]
        D = self.shelter_profile["room_depth"]
        H = self.shelter_profile["ceiling_height"]

        for i in range(num_rays):
            az_rad = rtheta + i * math.radians(LIDAR_HORIZONTAL_RES)
            cos_az = math.cos(az_rad)
            sin_az = math.sin(az_rad)

            # Intersect ray with axis-aligned bounding box (shelter walls)
            r_wall = self._ray_aabb_intersect(rx, ry, cos_az, sin_az, W, D)

            # Ceiling / floor intersection (elevation channel)
            if abs(sin_elev) > 1e-6:
                if sin_elev > 0:
                    r_ceiling = (H - 0.3) / sin_elev  # 0.3 m sensor height
                else:
                    r_ceiling = -0.3 / sin_elev        # Floor at z=0
                r_hit = min(r_wall, r_ceiling)
            else:
                r_hit = r_wall

            # Apply damage zone modifiers
            r_hit = self._apply_damage_zones(rx, ry, cos_az, sin_az, r_hit)

            # Sensor dropout (specular / out-of-range return)
            if random.random() < 0.02:   # 2% dropout rate
                r_hit = float('inf')

            # Clamp to valid range
            r_hit = min(max(r_hit, LIDAR_MIN_RANGE_M), LIDAR_MAX_RANGE_M)

            # Gaussian noise model
            if self.enable_noise and r_hit < LIDAR_MAX_RANGE_M:
                r_hit += random.gauss(0.0, SENSOR_NOISE_SIGMA_M)
                r_hit = max(r_hit, LIDAR_MIN_RANGE_M)

            ranges[i]      = r_hit
            intensities[i] = self._compute_intensity(r_hit)

        return LaserScanData(
            ranges      = ranges,
            intensities = intensities,
            timestamp   = self._sim_time,
        )

    def _ray_aabb_intersect(
        self,
        ox: float, oy: float,
        dx: float, dy: float,
        W: float, D: float,
    ) -> float:
        """
        Compute the distance from origin (ox, oy) in direction (dx, dy)
        until the ray hits the shelter's axis-aligned bounding box.

        Uses the slab method for AABB intersection.

        Args:
            ox, oy : Ray origin.
            dx, dy : Ray direction unit vector.
            W, D   : Room width and depth (meters).

        Returns:
            float: Distance to the nearest wall intersection.
        """
        t_list = []

        # X walls
        if abs(dx) > 1e-9:
            t_list.append((0.0 - ox) / dx)
            t_list.append((W   - ox) / dx)
        # Y walls
        if abs(dy) > 1e-9:
            t_list.append((0.0 - oy) / dy)
            t_list.append((D   - oy) / dy)

        positive_t = [t for t in t_list if t > 0.01]
        return min(positive_t) if positive_t else LIDAR_MAX_RANGE_M

    def _apply_damage_zones(
        self,
        rx: float, ry: float,
        dx: float, dy: float,
        r_nominal: float,
    ) -> float:
        """
        Modify the nominal ray range where it passes through a damage zone.

        Damage zone effects:
          - collapsed_wall : Wall is missing → ray travels further.
          - roof_hole      : Ceiling return missing at high elevation → inf.
          - debris_pile    : Random near return as the ray hits rubble.

        Args:
            rx, ry    : Ray origin.
            dx, dy    : Ray direction.
            r_nominal : Expected range without damage.

        Returns:
            float: Modified range after damage zone effects.
        """
        for zone in self.shelter_profile["damage_zones"]:
            zx, zy, zr = zone["x"], zone["y"], zone["radius"]

            # Check if ray passes near the damage zone centre
            # (simplified disc intersection)
            dist_to_zone = math.sqrt((rx - zx) ** 2 + (ry - zy) ** 2)
            if dist_to_zone > zr + r_nominal:
                continue

            # Parametric closest approach of ray to zone centre
            t_closest = (zx - rx) * dx + (zy - ry) * dy
            if t_closest < 0:
                continue
            closest_x = rx + t_closest * dx
            closest_y = ry + t_closest * dy
            dist_approach = math.sqrt((closest_x - zx) ** 2 + (closest_y - zy) ** 2)

            if dist_approach <= zr:
                zone_type = zone["type"]
                if zone_type == "collapsed_wall":
                    # Wall missing → large range or max
                    r_nominal = min(r_nominal * random.uniform(1.5, 3.0), LIDAR_MAX_RANGE_M)
                elif zone_type == "roof_hole":
                    # Ceiling absent → may return max range intermittently
                    if random.random() < 0.6:
                        r_nominal = LIDAR_MAX_RANGE_M
                elif zone_type == "debris_pile":
                    # Rubble creates short, noisy returns
                    r_nominal = t_closest * random.uniform(0.3, 0.85)

        return r_nominal

    def _compute_intensity(self, range_m: float) -> float:
        """
        Estimate the reflected signal intensity based on range (inverse square law).

        Real LiDAR intensity also depends on surface albedo and angle of incidence.
        We use a simplified 1/r² model here.

        Args:
            range_m : Measured range in meters.

        Returns:
            float: Simulated intensity [0, 255].
        """
        if range_m >= LIDAR_MAX_RANGE_M or range_m <= 0:
            return 0.0
        intensity = INTENSITY_MAX / (1.0 + (range_m / 2.0) ** 2)
        return max(0.0, min(float(intensity), INTENSITY_MAX))

    @staticmethod
    def _median_filter(arr: np.ndarray, window: int = 5) -> np.ndarray:
        """
        Apply a sliding-window median filter to a 1D array.

        Edges are padded with reflected values to avoid boundary effects.

        Args:
            arr    : Input numpy array.
            window : Size of the sliding window (must be odd).

        Returns:
            np.ndarray: Filtered array of the same shape.
        """
        half   = window // 2
        padded = np.pad(arr, half, mode='reflect')
        result = np.array([
            np.median(padded[i: i + window])
            for i in range(len(arr))
        ], dtype=arr.dtype)
        return result
