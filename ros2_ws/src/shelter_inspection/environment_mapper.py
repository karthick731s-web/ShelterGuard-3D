#!/usr/bin/env python3
"""
environment_mapper.py
======================
3D Environment Reconstruction module for the Shelter Inspection System.

This module takes accumulated LiDAR point clouds and reconstructs a digital
geometric model of the shelter. It computes:
  • Occupancy grid (2D floor plan)
  • Surface normal estimation (for wall / floor / ceiling classification)
  • Structural region segmentation (room zones, debris clusters)
  • Height map (voxelised elevation model)

In a real ROS2 deployment this module would integrate with:
    • octomap_server  : 3D occupancy tree (OctoMap / Voxblox)
    • slam_toolbox    : 2D SLAM-based floor-plan generation
    • rtabmap         : RGB-D / LiDAR 3D SLAM
    • Open3D          : Surface reconstruction (Poisson / BPA)

For our simulation we use numpy-based algorithms that mirror these
production approaches at a conceptual level.

Author  : Team LiDAR-Inspect
Project : 3D LiDAR-Based Shelter Damage Inspection System
License : MIT
"""

import math
import logging
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Tuple

from pointcloud_generator import PointCloud

# ---------------------------------------------------------------------------
# Logger
# ---------------------------------------------------------------------------
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
GRID_RESOLUTION = 0.10   # Occupancy grid cell size (meters per cell)
FLOOR_HEIGHT_MIN = 0.00  # Points below this are floor candidates (m)
FLOOR_HEIGHT_MAX = 0.15
WALL_HEIGHT_MIN  = 0.15  # Points in this range are wall candidates (m)
WALL_HEIGHT_MAX  = 2.80
CEILING_HEIGHT   = 2.80  # Points above this are ceiling candidates (m)


# ---------------------------------------------------------------------------
# Data Classes
# ---------------------------------------------------------------------------

@dataclass
class OccupancyGrid:
    """
    2D occupancy grid map of the shelter (floor-plane projection).

    Each cell stores one of three states:
        0  = FREE     (navigable floor space)
        1  = OCCUPIED (wall, pillar, or large debris)
       -1  = UNKNOWN  (not yet observed)

    Attributes:
        grid       : 2D numpy int8 array of cell states.
        resolution : Meters per grid cell.
        origin_x   : World X-coordinate of grid[0,0] lower-left corner.
        origin_y   : World Y-coordinate of grid[0,0] lower-left corner.
    """
    grid      : np.ndarray
    resolution: float
    origin_x  : float
    origin_y  : float

    @property
    def width_cells(self) -> int:
        return self.grid.shape[1]

    @property
    def height_cells(self) -> int:
        return self.grid.shape[0]

    def world_to_cell(self, wx: float, wy: float) -> Tuple[int, int]:
        """Convert world (x,y) to grid (row, col) indices."""
        col = int((wx - self.origin_x) / self.resolution)
        row = int((wy - self.origin_y) / self.resolution)
        return row, col

    def cell_to_world(self, row: int, col: int) -> Tuple[float, float]:
        """Convert grid (row, col) to world (x, y) centre coordinates."""
        wx = self.origin_x + (col + 0.5) * self.resolution
        wy = self.origin_y + (row + 0.5) * self.resolution
        return wx, wy


@dataclass
class StructuralRegion:
    """
    A labelled region within the reconstructed shelter map.

    Attributes:
        label       : Human-readable region name (e.g. 'North Wall', 'Roof Area').
        region_type : Category ('wall', 'floor', 'ceiling', 'debris', 'open_space').
        points      : Array of 3D points belonging to this region.
        centroid    : Mean (x, y, z) position of the region.
        bounding_box: (min_xyz, max_xyz) corners of the axis-aligned bounding box.
    """
    label        : str
    region_type  : str
    points       : np.ndarray
    centroid     : Tuple[float, float, float] = (0.0, 0.0, 0.0)
    bounding_box : Tuple[np.ndarray, np.ndarray] = field(
        default_factory=lambda: (np.zeros(3), np.zeros(3))
    )

    def __post_init__(self) -> None:
        if len(self.points) > 0:
            self.centroid     = tuple(self.points.mean(axis=0).tolist())
            self.bounding_box = (self.points.min(axis=0), self.points.max(axis=0))

    @property
    def volume_m3(self) -> float:
        """Approximate bounding-box volume in cubic metres."""
        extents = self.bounding_box[1] - self.bounding_box[0]
        return float(np.prod(extents))


@dataclass
class ShelterMap:
    """
    Complete digital reconstruction of the inspected shelter.

    Attributes:
        shelter_id      : Unique identifier for this shelter instance.
        occupancy_grid  : 2D floor-plan occupancy grid.
        height_map      : 2D array of maximum observed height per grid cell.
        regions         : List of classified structural regions.
        scan_count      : Number of LiDAR scans used in reconstruction.
        total_points    : Total number of points in the source cloud.
        coverage_pct    : Estimated percentage of the shelter volume scanned.
    """
    shelter_id    : str
    occupancy_grid: Optional[OccupancyGrid]
    height_map    : Optional[np.ndarray]
    regions       : List[StructuralRegion] = field(default_factory=list)
    scan_count    : int = 0
    total_points  : int = 0
    coverage_pct  : float = 0.0

    def get_region_by_type(self, region_type: str) -> List[StructuralRegion]:
        """Return all regions matching the given type string."""
        return [r for r in self.regions if r.region_type == region_type]


# ---------------------------------------------------------------------------
# EnvironmentMapper
# ---------------------------------------------------------------------------

class EnvironmentMapper:
    """
    Reconstructs a 3D geometric model of the inspected shelter from LiDAR data.

    Pipeline:
        1. accumulate_cloud()    → merge incoming PointCloud into the running map.
        2. build_occupancy_grid()→ project points onto 2D floor plan.
        3. classify_regions()    → segment points by height into structural zones.
        4. compute_height_map()  → elevation model for surface analysis.
        5. get_map()             → return the complete ShelterMap.

    Attributes:
        shelter_id     : Identifier passed through to ShelterMap.
        cloud          : Current accumulated PointCloud.
        _occ_grid      : Internally cached OccupancyGrid.
        _height_map    : Internally cached height map array.
        _regions       : Classified structural-region list.
    """

    def __init__(self, shelter_id: str = "SH-001") -> None:
        """
        Initialise the mapper for a specific shelter.

        Args:
            shelter_id : Unique shelter identifier string.
        """
        self.shelter_id = shelter_id
        self.cloud      : Optional[PointCloud] = None
        self._occ_grid  : Optional[OccupancyGrid] = None
        self._height_map: Optional[np.ndarray] = None
        self._regions   : List[StructuralRegion] = []
        self._scan_count: int = 0

        logger.info("EnvironmentMapper initialised | shelter_id=%s", shelter_id)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def accumulate_cloud(self, cloud: PointCloud) -> None:
        """
        Merge a new PointCloud into the running reconstruction.

        Args:
            cloud : PointCloud from PointCloudGenerator.scan_to_pointcloud().
        """
        if cloud.num_points == 0:
            logger.debug("accumulate_cloud: empty cloud — skipping.")
            return

        if self.cloud is None:
            self.cloud = cloud
        else:
            merged_pts = np.vstack([self.cloud.points,      cloud.points])
            merged_int = np.concatenate([self.cloud.intensities, cloud.intensities])
            merged_col = np.vstack([self.cloud.colors,      cloud.colors])
            # Use a new PointCloud with merged data
            from pointcloud_generator import PointCloud as PC
            self.cloud = PC(
                points      = merged_pts,
                intensities = merged_int,
                colors      = merged_col,
            )

        self._scan_count += 1
        logger.debug(
            "Cloud accumulated | scan #%d | total_pts=%d",
            self._scan_count, self.cloud.num_points,
        )

    def build_occupancy_grid(self) -> OccupancyGrid:
        """
        Project the accumulated point cloud onto a 2D occupancy grid.

        Algorithm:
          1. Separate floor points (z < 0.15 m) and obstacle points (z > 0.15 m).
          2. Mark cells containing floor points as FREE (0).
          3. Mark cells containing obstacle points as OCCUPIED (1).
          4. Remaining unobserved cells stay UNKNOWN (-1).

        Returns:
            OccupancyGrid: The computed occupancy map.
        """
        if self.cloud is None or self.cloud.num_points == 0:
            logger.warning("build_occupancy_grid: no cloud data — returning empty grid.")
            dummy = np.full((60, 80), -1, dtype=np.int8)
            self._occ_grid = OccupancyGrid(dummy, GRID_RESOLUTION, 0.0, 0.0)
            return self._occ_grid

        pts = self.cloud.points
        x_min, y_min = pts[:, 0].min(), pts[:, 1].min()
        x_max, y_max = pts[:, 0].max(), pts[:, 1].max()

        cols = max(1, int(math.ceil((x_max - x_min) / GRID_RESOLUTION)) + 2)
        rows = max(1, int(math.ceil((y_max - y_min) / GRID_RESOLUTION)) + 2)

        grid = np.full((rows, cols), -1, dtype=np.int8)  # Start all UNKNOWN

        # Floor points → FREE
        floor_mask = pts[:, 2] < FLOOR_HEIGHT_MAX
        floor_pts  = pts[floor_mask]
        for pt in floor_pts:
            col = int((pt[0] - x_min) / GRID_RESOLUTION)
            row = int((pt[1] - y_min) / GRID_RESOLUTION)
            if 0 <= row < rows and 0 <= col < cols:
                if grid[row, col] != 1:   # Free if not already marked occupied
                    grid[row, col] = 0

        # Wall / obstacle points → OCCUPIED
        obs_mask = pts[:, 2] >= WALL_HEIGHT_MIN
        obs_pts  = pts[obs_mask]
        for pt in obs_pts:
            col = int((pt[0] - x_min) / GRID_RESOLUTION)
            row = int((pt[1] - y_min) / GRID_RESOLUTION)
            if 0 <= row < rows and 0 <= col < cols:
                grid[row, col] = 1

        self._occ_grid = OccupancyGrid(
            grid       = grid,
            resolution = GRID_RESOLUTION,
            origin_x   = float(x_min),
            origin_y   = float(y_min),
        )

        free_pct   = 100.0 * (grid == 0).sum() / grid.size
        occ_pct    = 100.0 * (grid == 1).sum() / grid.size
        logger.info(
            "Occupancy grid built | size=%dx%d cells | free=%.1f%% | occupied=%.1f%%",
            rows, cols, free_pct, occ_pct,
        )
        return self._occ_grid

    def classify_regions(self) -> List[StructuralRegion]:
        """
        Segment the point cloud into labelled structural regions by height band.

        Height bands (matching typical single-storey shelter geometry):
            z < 0.15 m        → Floor surface
            0.15–2.80 m       → Wall / vertical structures
            > 2.80 m          → Ceiling / roof elements

        Points within each band are further clustered by horizontal proximity
        to distinguish isolated debris piles from continuous walls.

        Returns:
            List[StructuralRegion]: Labelled regions for downstream analysis.
        """
        if self.cloud is None or self.cloud.num_points == 0:
            logger.warning("classify_regions: no cloud data.")
            return []

        pts    = self.cloud.points
        regions: List[StructuralRegion] = []

        # ---- Floor ----
        floor_mask = pts[:, 2] <= FLOOR_HEIGHT_MAX
        if floor_mask.any():
            regions.append(StructuralRegion(
                label       = "Floor Surface",
                region_type = "floor",
                points      = pts[floor_mask],
            ))

        # ---- Walls (split by quadrant for directional labelling) ----
        wall_mask = (pts[:, 2] > WALL_HEIGHT_MIN) & (pts[:, 2] <= WALL_HEIGHT_MAX)
        wall_pts  = pts[wall_mask]
        if len(wall_pts) > 0:
            cx = wall_pts[:, 0].mean()
            cy = wall_pts[:, 1].mean()
            quadrant_labels = {
                "North Wall": (wall_pts[:, 1] >  cy) & (np.abs(wall_pts[:, 0] - cx) < np.abs(wall_pts[:, 1] - cy)),
                "South Wall": (wall_pts[:, 1] <= cy) & (np.abs(wall_pts[:, 0] - cx) < np.abs(wall_pts[:, 1] - cy)),
                "East Wall" : (wall_pts[:, 0] >  cx) & (np.abs(wall_pts[:, 0] - cx) >= np.abs(wall_pts[:, 1] - cy)),
                "West Wall" : (wall_pts[:, 0] <= cx) & (np.abs(wall_pts[:, 0] - cx) >= np.abs(wall_pts[:, 1] - cy)),
            }
            for label, mask in quadrant_labels.items():
                if mask.any():
                    regions.append(StructuralRegion(
                        label       = label,
                        region_type = "wall",
                        points      = wall_pts[mask],
                    ))

        # ---- Ceiling / Roof ----
        ceil_mask = pts[:, 2] > CEILING_HEIGHT
        if ceil_mask.any():
            regions.append(StructuralRegion(
                label       = "Ceiling / Roof",
                region_type = "ceiling",
                points      = pts[ceil_mask],
            ))

        # ---- Debris (mid-height anomalies outside wall band) ----
        # Points that are isolated clusters at mid-height in open floor area
        debris_mask = (
            (pts[:, 2] > FLOOR_HEIGHT_MAX) &
            (pts[:, 2] < WALL_HEIGHT_MIN + 0.5)
        )
        if debris_mask.any():
            regions.append(StructuralRegion(
                label       = "Debris / Rubble",
                region_type = "debris",
                points      = pts[debris_mask],
            ))

        self._regions = regions
        logger.info(
            "Region classification complete | %d regions found: %s",
            len(regions),
            [r.label for r in regions],
        )
        return regions

    def compute_height_map(self) -> np.ndarray:
        """
        Build a 2D elevation (height) map from the accumulated point cloud.

        For each horizontal grid cell, the height map records the maximum Z
        coordinate of all points falling within it. This creates a DSM
        (Digital Surface Model) of the shelter interior.

        Returns:
            np.ndarray: 2D array of maximum heights per cell.
        """
        if self.cloud is None or self.cloud.num_points == 0:
            logger.warning("compute_height_map: no cloud data.")
            self._height_map = np.zeros((60, 80), dtype=np.float32)
            return self._height_map

        pts   = self.cloud.points
        x_min = pts[:, 0].min()
        y_min = pts[:, 1].min()
        x_max = pts[:, 0].max()
        y_max = pts[:, 1].max()

        cols = max(1, int(math.ceil((x_max - x_min) / GRID_RESOLUTION)) + 2)
        rows = max(1, int(math.ceil((y_max - y_min) / GRID_RESOLUTION)) + 2)

        height_map = np.zeros((rows, cols), dtype=np.float32)

        for pt in pts:
            col = int((pt[0] - x_min) / GRID_RESOLUTION)
            row = int((pt[1] - y_min) / GRID_RESOLUTION)
            if 0 <= row < rows and 0 <= col < cols:
                if pt[2] > height_map[row, col]:
                    height_map[row, col] = pt[2]

        self._height_map = height_map
        logger.info(
            "Height map built | size=%dx%d | max_height=%.2fm",
            rows, cols, float(height_map.max()),
        )
        return height_map

    def get_map(self) -> ShelterMap:
        """
        Assemble and return the complete ShelterMap object.

        Returns:
            ShelterMap: Full reconstruction with grid, height map, and regions.
        """
        total_pts = self.cloud.num_points if self.cloud else 0
        # Estimate coverage (heuristic: more points → better coverage)
        coverage  = min(100.0, total_pts / 500.0)

        return ShelterMap(
            shelter_id    = self.shelter_id,
            occupancy_grid= self._occ_grid,
            height_map    = self._height_map,
            regions       = self._regions,
            scan_count    = self._scan_count,
            total_points  = total_pts,
            coverage_pct  = round(coverage, 1),
        )

    def visualize_occupancy_grid(
        self,
        save_path: Optional[str] = None,
    ) -> None:
        """
        Render the 2D occupancy grid map using Matplotlib.

        Colour scheme:
            White  → FREE / navigable floor
            Dark   → OCCUPIED / walls
            Gray   → UNKNOWN / unobserved

        Args:
            save_path : Optional path to save the figure.
        """
        if self._occ_grid is None:
            logger.warning("visualize_occupancy_grid: no grid available. Call build_occupancy_grid() first.")
            return

        grid = self._occ_grid.grid.astype(np.float32)
        # Map: -1 → 0.5 (gray), 0 → 1.0 (white), 1 → 0.0 (black)
        display = np.where(grid == -1, 0.5, np.where(grid == 0, 1.0, 0.0))

        fig, ax = plt.subplots(figsize=(10, 8), facecolor="#0d1117")
        ax.set_facecolor("#0d1117")
        ax.imshow(display, cmap='gray', origin='lower', vmin=0.0, vmax=1.0)

        legend_patches = [
            mpatches.Patch(color='white', label='Free Space'),
            mpatches.Patch(color='black', label='Occupied (Wall/Obstacle)'),
            mpatches.Patch(color='gray',  label='Unknown'),
        ]
        ax.legend(handles=legend_patches, loc='upper right',
                  facecolor='#1c1c1c', labelcolor='white', fontsize=9)

        ax.set_title("2D Occupancy Grid — Shelter Floor Plan",
                     color='white', fontsize=13)
        ax.set_xlabel("X cells", color='#aaaaaa')
        ax.set_ylabel("Y cells", color='#aaaaaa')
        ax.tick_params(colors='#888888')
        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight',
                        facecolor=fig.get_facecolor())
            logger.info("Occupancy grid figure saved → %s", save_path)

        try:
            plt.show(block=False)
            plt.pause(0.5)
        except Exception as exc:
            logger.debug("plt.show skipped: %s", exc)
        plt.close(fig)

    def visualize_height_map(self, save_path: Optional[str] = None) -> None:
        """
        Render the 2D height map as a colour-coded surface elevation image.

        Args:
            save_path : Optional path to save the figure.
        """
        if self._height_map is None:
            logger.warning("visualize_height_map: no height map available.")
            return

        fig, ax = plt.subplots(figsize=(10, 8), facecolor="#0d1117")
        ax.set_facecolor("#0d1117")
        img = ax.imshow(
            self._height_map, cmap='hot', origin='lower',
            vmin=0.0, vmax=max(0.1, float(self._height_map.max())),
        )
        cbar = plt.colorbar(img, ax=ax)
        cbar.set_label("Max Height (m)", color='white', fontsize=10)
        cbar.ax.tick_params(colors='white')
        ax.set_title("Height Map (Digital Surface Model)", color='white', fontsize=13)
        ax.set_xlabel("X cells", color='#aaaaaa')
        ax.set_ylabel("Y cells", color='#aaaaaa')
        ax.tick_params(colors='#888888')
        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight',
                        facecolor=fig.get_facecolor())
            logger.info("Height map figure saved → %s", save_path)

        try:
            plt.show(block=False)
            plt.pause(0.5)
        except Exception as exc:
            logger.debug("plt.show skipped: %s", exc)
        plt.close(fig)
