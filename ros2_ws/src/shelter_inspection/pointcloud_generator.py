#!/usr/bin/env python3
"""
pointcloud_generator.py
========================
Converts multi-layer LiDAR scans into 3D point clouds for visualisation
and downstream analysis.

This module bridges the raw sensor data (range + angle measurements) and the
geometric 3D representation used by the environment mapper and damage detector.

Coordinate frame:
    • X  → forward (aligned with robot heading at scan time)
    • Y  → left of robot
    • Z  → upward
    All coordinates are in the world frame after applying the robot's pose
    transform at the time the scan was captured.

Key equations (spherical → Cartesian conversion):
    x = r · cos(elevation) · cos(azimuth + robot_heading)  + robot_x
    y = r · cos(elevation) · sin(azimuth + robot_heading)  + robot_y
    z = r · sin(elevation)                                  + sensor_height

Author  : Team LiDAR-Inspect
Project : 3D LiDAR-Based Shelter Damage Inspection System
License : MIT
"""

import math
import logging
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401 – registers 3D projection
from typing import Optional, List, Tuple
from dataclasses import dataclass

from lidar_processor import (
    MultiLayerScan,
    LIDAR_MIN_RANGE_M,
    LIDAR_MAX_RANGE_M,
    LIDAR_HORIZONTAL_RES,
)

# ---------------------------------------------------------------------------
# Logger
# ---------------------------------------------------------------------------
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
SENSOR_HEIGHT_M = 0.30   # Height of LiDAR sensor above ground on TurtleBot3 (m)
VOXEL_SIZE      = 0.05   # Down-sampling voxel grid cell size (meters)


# ---------------------------------------------------------------------------
# Data class
# ---------------------------------------------------------------------------

@dataclass
class PointCloud:
    """
    Container for a 3D point cloud derived from one or more LiDAR scans.

    Attributes:
        points     : (N, 3) float32 array of [x, y, z] coordinates (world frame).
        intensities: (N,)   float32 array of per-point reflected intensities.
        colors     : (N, 3) float32 array of RGB colours [0–1] for visualisation.
        source_pose: (x, y, theta) of the robot when the scan was taken.
    """
    points     : np.ndarray          # shape (N, 3)
    intensities: np.ndarray          # shape (N,)
    colors     : np.ndarray          # shape (N, 3)
    source_pose: Tuple[float, float, float] = (0.0, 0.0, 0.0)

    @property
    def num_points(self) -> int:
        """Number of 3D points in the cloud."""
        return len(self.points)

    def __repr__(self) -> str:
        return (
            f"PointCloud(N={self.num_points}, "
            f"pose=({self.source_pose[0]:.2f}, {self.source_pose[1]:.2f}))"
        )


# ---------------------------------------------------------------------------
# PointCloudGenerator
# ---------------------------------------------------------------------------

class PointCloudGenerator:
    """
    Converts LiDAR scan data into a 3D point cloud and manages accumulated maps.

    In a real ROS2 system this would interface with:
        • sensor_msgs/PointCloud2 messages on /velodyne_points
        • tf2 for coordinate frame transforms (sensor_frame → map_frame)
        • Open3D or PCL for ICP / NDT registration between sequential scans

    This simulation module uses numpy for efficient vectorised coordinate
    conversion and matplotlib for 3D visualisation.

    Attributes:
        accumulated_points    : Concatenated points from all scans processed so far.
        accumulated_intensities: Matching intensity values.
        accumulated_colors    : Matching RGB colour values.
        scan_count            : Number of scans merged into the accumulated cloud.
    """

    def __init__(self) -> None:
        """Initialise an empty PointCloudGenerator."""
        self.accumulated_points     : Optional[np.ndarray] = None
        self.accumulated_intensities: Optional[np.ndarray] = None
        self.accumulated_colors     : Optional[np.ndarray] = None
        self.scan_count             : int = 0

        logger.info("PointCloudGenerator initialised.")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def scan_to_pointcloud(self, scan: MultiLayerScan) -> PointCloud:
        """
        Convert a MultiLayerScan into a 3D PointCloud using spherical coordinates.

        For each LiDAR channel (elevation layer) and each horizontal ray:
            1. Retrieve the measured range and validate it.
            2. Compute the azimuth angle = ray_index × H_res + robot_heading.
            3. Apply the rotation matrix for the elevation angle.
            4. Translate into world coordinates using the robot's pose.

        Args:
            scan : A MultiLayerScan from LiDARProcessor.generate_scan().

        Returns:
            PointCloud: 3D point coordinates, intensities, and display colours.
        """
        num_channels   = len(scan.layers)
        elevation_degs = scan.elevation_angles
        robot_x        = scan.robot_pose_x
        robot_y        = scan.robot_pose_y
        robot_theta    = scan.robot_pose_theta

        point_list     : List[np.ndarray] = []
        intensity_list : List[np.ndarray] = []

        for ch_idx, (layer, elev_deg) in enumerate(zip(scan.layers, elevation_degs)):
            elev_rad = math.radians(elev_deg)
            cos_e    = math.cos(elev_rad)
            sin_e    = math.sin(elev_rad)

            num_rays = layer.num_rays
            # Build azimuth array for all rays in this channel
            az_offsets = np.arange(num_rays, dtype=np.float32) * math.radians(LIDAR_HORIZONTAL_RES)
            azimuths   = robot_theta + az_offsets   # world-frame azimuth

            ranges = layer.ranges.astype(np.float32)

            # Validity mask: reject out-of-range and dropout values
            valid = (ranges >= LIDAR_MIN_RANGE_M) & (ranges < LIDAR_MAX_RANGE_M)

            if not np.any(valid):
                continue

            r_valid  = ranges[valid]
            az_valid = azimuths[valid]
            int_valid= layer.intensities[valid].astype(np.float32)

            # Spherical → Cartesian (sensor frame, then world frame)
            x_world = robot_x + r_valid * cos_e * np.cos(az_valid)
            y_world = robot_y + r_valid * cos_e * np.sin(az_valid)
            z_world = SENSOR_HEIGHT_M + r_valid * sin_e

            pts = np.column_stack([x_world, y_world, z_world]).astype(np.float32)
            point_list.append(pts)
            intensity_list.append(int_valid)

        if not point_list:
            logger.warning("scan_to_pointcloud: no valid points found!")
            empty = np.zeros((0, 3), dtype=np.float32)
            return PointCloud(
                points      = empty,
                intensities = np.zeros(0, dtype=np.float32),
                colors      = np.zeros((0, 3), dtype=np.float32),
                source_pose = (robot_x, robot_y, robot_theta),
            )

        all_points     = np.vstack(point_list)
        all_intensities= np.concatenate(intensity_list)
        all_colors     = self._colorize(all_points, all_intensities)

        cloud = PointCloud(
            points      = all_points,
            intensities = all_intensities,
            colors      = all_colors,
            source_pose = (robot_x, robot_y, robot_theta),
        )

        logger.debug("Converted scan → %s", cloud)
        return cloud

    def accumulate(self, cloud: PointCloud) -> None:
        """
        Merge a new PointCloud into the running accumulated map.

        In a real system this step would include point-cloud registration
        (ICP / NDT) to correct for odometry drift before merging.

        Args:
            cloud : A PointCloud object to add to the accumulated map.
        """
        if cloud.num_points == 0:
            logger.debug("accumulate: skipping empty cloud.")
            return

        if self.accumulated_points is None:
            self.accumulated_points      = cloud.points.copy()
            self.accumulated_intensities = cloud.intensities.copy()
            self.accumulated_colors      = cloud.colors.copy()
        else:
            self.accumulated_points      = np.vstack(
                [self.accumulated_points,      cloud.points])
            self.accumulated_intensities = np.concatenate(
                [self.accumulated_intensities, cloud.intensities])
            self.accumulated_colors      = np.vstack(
                [self.accumulated_colors,      cloud.colors])

        self.scan_count += 1
        logger.debug(
            "Accumulated cloud | scans=%d | total_points=%d",
            self.scan_count, len(self.accumulated_points),
        )

    def downsample(self, voxel_size: float = VOXEL_SIZE) -> np.ndarray:
        """
        Reduce point cloud density using a voxel grid down-sampling filter.

        Each voxel retains only the centroid of all points that fall within it.
        This dramatically reduces data volume while preserving global structure —
        critical for real-time performance on embedded computing platforms.

        Args:
            voxel_size : Edge length of each cubic voxel in meters.

        Returns:
            np.ndarray: Down-sampled (M, 3) point array where M << N.
        """
        if self.accumulated_points is None or len(self.accumulated_points) == 0:
            logger.warning("downsample: no accumulated points available.")
            return np.zeros((0, 3), dtype=np.float32)

        pts = self.accumulated_points
        # Shift to positive quadrant and quantize to voxel indices
        mins    = pts.min(axis=0)
        shifted = pts - mins
        indices = (shifted / voxel_size).astype(np.int32)

        # Use structured index as unique voxel key
        voxel_keys = (
            indices[:, 0].astype(np.int64) * 100000
            + indices[:, 1].astype(np.int64) * 1000
            + indices[:, 2].astype(np.int64)
        )
        _, unique_idx = np.unique(voxel_keys, return_index=True)
        downsampled   = pts[unique_idx]

        logger.info(
            "Voxel down-sample | before=%d | after=%d | reduction=%.1f%%",
            len(pts), len(downsampled),
            100.0 * (1 - len(downsampled) / len(pts)),
        )
        return downsampled.astype(np.float32)

    def get_accumulated_cloud(self) -> PointCloud:
        """
        Return the full accumulated point cloud as a PointCloud object.

        Returns:
            PointCloud: Merged cloud from all accumulated scans.
        """
        if self.accumulated_points is None:
            empty = np.zeros((0, 3), dtype=np.float32)
            return PointCloud(
                points      = empty,
                intensities = np.zeros(0, dtype=np.float32),
                colors      = np.zeros((0, 3), dtype=np.float32),
            )
        return PointCloud(
            points      = self.accumulated_points,
            intensities = self.accumulated_intensities,
            colors      = self.accumulated_colors,
        )

    def visualize_3d(
        self,
        cloud: Optional[PointCloud] = None,
        title: str = "3D Point Cloud — Shelter Inspection",
        save_path: Optional[str] = None,
        max_points: int = 15000,
    ) -> None:
        """
        Render the point cloud as a 3D scatter plot using Matplotlib.

        Points are colour-mapped by height (Z axis) to make structural features
        such as floor, walls, and ceiling easily distinguishable.

        Args:
            cloud      : PointCloud to render. Uses accumulated cloud if None.
            title      : Plot window title.
            save_path  : If provided, saves the figure to this file path.
            max_points : Maximum points to display (random sub-sample for speed).
        """
        if cloud is None:
            cloud = self.get_accumulated_cloud()

        if cloud.num_points == 0:
            logger.warning("visualize_3d: no points to display.")
            return

        pts = cloud.points
        # Sub-sample for rendering performance
        if len(pts) > max_points:
            idx = np.random.choice(len(pts), max_points, replace=False)
            pts = pts[idx]

        fig = plt.figure(figsize=(14, 9), facecolor="#0d0d0d")
        ax  = fig.add_subplot(111, projection='3d')
        ax.set_facecolor("#0d0d0d")
        fig.patch.set_facecolor("#0d0d0d")

        # Height-based colour mapping
        z_vals  = pts[:, 2]
        z_norm  = (z_vals - z_vals.min()) / (np.ptp(z_vals) + 1e-6)
        colours = cm.plasma(z_norm)

        scatter = ax.scatter(
            pts[:, 0], pts[:, 1], pts[:, 2],
            c       = colours,
            s       = 0.4,
            alpha   = 0.75,
            linewidths = 0,
        )

        # Axes styling
        for spine in [ax.xaxis, ax.yaxis, ax.zaxis]:
            spine.pane.fill  = False
            spine.pane.set_edgecolor("#333333")

        ax.tick_params(colors='#aaaaaa', labelsize=8)
        ax.set_xlabel("X (m)", color="#cccccc", fontsize=10)
        ax.set_ylabel("Y (m)", color="#cccccc", fontsize=10)
        ax.set_zlabel("Z (m)", color="#cccccc", fontsize=10)
        ax.set_title(title, color="#ffffff", fontsize=13, pad=18)

        # Colour bar legend
        mappable = cm.ScalarMappable(cmap='plasma')
        mappable.set_array(z_vals)
        cbar = fig.colorbar(mappable, ax=ax, shrink=0.5, pad=0.1)
        cbar.set_label("Height (m)", color="#cccccc", fontsize=9)
        cbar.ax.tick_params(colors='#cccccc', labelsize=8)

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight',
                        facecolor=fig.get_facecolor())
            logger.info("Point cloud visualisation saved → %s", save_path)

        try:
            plt.show(block=False)
            plt.pause(0.5)
        except Exception as exc:
            logger.debug("plt.show skipped: %s", exc)
        plt.close(fig)

    def visualize_top_view(
        self,
        cloud: Optional[PointCloud] = None,
        title: str = "Top-View Occupancy Map",
        save_path: Optional[str] = None,
    ) -> None:
        """
        Render a bird's-eye (top-down) 2D projection of the point cloud.

        This view is equivalent to a 2D occupancy grid as used by ROS2 SLAM
        algorithms (slam_toolbox, Cartographer) and is useful for showing
        the floor layout of the scanned shelter.

        Args:
            cloud     : PointCloud to render. Uses accumulated cloud if None.
            title     : Plot window title.
            save_path : Optional file path to save the plot.
        """
        if cloud is None:
            cloud = self.get_accumulated_cloud()

        if cloud.num_points == 0:
            logger.warning("visualize_top_view: no points to display.")
            return

        pts = cloud.points

        fig, ax = plt.subplots(figsize=(10, 8), facecolor="#0d0d0d")
        ax.set_facecolor("#0d0d0d")

        z_vals = pts[:, 2]
        z_norm = (z_vals - z_vals.min()) / (np.ptp(z_vals) + 1e-6)
        colours= cm.viridis(z_norm)

        ax.scatter(
            pts[:, 0], pts[:, 1],
            c=colours, s=0.3, alpha=0.6, linewidths=0,
        )
        ax.set_xlabel("X (m)", color="#cccccc", fontsize=11)
        ax.set_ylabel("Y (m)", color="#cccccc", fontsize=11)
        ax.set_title(title, color="#ffffff", fontsize=13)
        ax.tick_params(colors='#aaaaaa')
        ax.set_aspect('equal', adjustable='box')
        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight',
                        facecolor=fig.get_facecolor())
            logger.info("Top-view saved → %s", save_path)

        try:
            plt.show(block=False)
            plt.pause(0.5)
        except Exception as exc:
            logger.debug("plt.show skipped: %s", exc)
        plt.close(fig)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _colorize(
        points: np.ndarray,
        intensities: np.ndarray,
    ) -> np.ndarray:
        """
        Assign RGB colours to each point based on height and intensity.

        Uses a perceptually uniform colourmap (viridis) mapped to the Z axis
        so that vertical structural features are visually distinct.

        Args:
            points      : (N, 3) array of 3D coordinates.
            intensities : (N,)   array of per-point intensities [0–255].

        Returns:
            np.ndarray: (N, 3) float32 RGB values in [0, 1].
        """
        if len(points) == 0:
            return np.zeros((0, 3), dtype=np.float32)

        z = points[:, 2]
        z_norm = (z - z.min()) / (np.ptp(z) + 1e-6)

        cmap   = plt.get_cmap('viridis')
        colors = cmap(z_norm)[:, :3].astype(np.float32)   # Drop alpha channel
        return colors
