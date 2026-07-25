#!/usr/bin/env python3
"""
robot_controller.py
====================
ROS2-compatible robot controller for TurtleBot3 autonomous navigation.

This module simulates autonomous navigation of a TurtleBot3 robot inside a
damaged shelter environment. In a real deployment, this module would interface
with ROS2 topics (cmd_vel, odom, tf) to physically drive the robot.

Author  : Team LiDAR-Inspect
Project : 3D LiDAR-Based Shelter Damage Inspection System
License : MIT
"""

import time
import math
import logging
import random
from typing import Tuple, List, Optional
from dataclasses import dataclass, field

# ---------------------------------------------------------------------------
# Configure module-level logger
# ---------------------------------------------------------------------------
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


# ---------------------------------------------------------------------------
# Data Classes
# ---------------------------------------------------------------------------

@dataclass
class Pose:
    """
    Represents the 2D pose (position + heading) of the robot on the floor plane.

    Attributes:
        x     : X-coordinate in meters (world frame).
        y     : Y-coordinate in meters (world frame).
        theta : Heading angle in radians (0 = +X axis, CCW positive).
    """
    x: float = 0.0
    y: float = 0.0
    theta: float = 0.0

    def __repr__(self) -> str:
        return f"Pose(x={self.x:.3f}, y={self.y:.3f}, theta={math.degrees(self.theta):.1f}°)"


@dataclass
class NavigationPath:
    """
    Stores the sequence of waypoints the robot has visited during inspection.

    Attributes:
        waypoints : Ordered list of Pose objects representing the travel history.
    """
    waypoints: List[Pose] = field(default_factory=list)

    def add(self, pose: Pose) -> None:
        """Append a new waypoint to the navigation path."""
        self.waypoints.append(Pose(pose.x, pose.y, pose.theta))

    def total_distance(self) -> float:
        """
        Compute the total Euclidean distance traveled along the recorded path.

        Returns:
            float: Total path length in meters.
        """
        if len(self.waypoints) < 2:
            return 0.0
        dist = 0.0
        for i in range(1, len(self.waypoints)):
            dx = self.waypoints[i].x - self.waypoints[i - 1].x
            dy = self.waypoints[i].y - self.waypoints[i - 1].y
            dist += math.sqrt(dx * dx + dy * dy)
        return dist


# ---------------------------------------------------------------------------
# RobotController Class
# ---------------------------------------------------------------------------

class RobotController:
    """
    Simulates the motion and navigation of a TurtleBot3 robot inside a shelter.

    In a real ROS2 system this class would:
      - Publish geometry_msgs/Twist to /cmd_vel for velocity commands.
      - Subscribe to nav_msgs/Odometry on /odom for pose feedback.
      - Interface with the Navigation2 (Nav2) stack for path planning.

    For simulation purposes, motion is modelled with simple kinematic equations
    and randomised obstacle avoidance to mimic realistic navigation behaviour
    inside a cluttered, structurally compromised building.

    Attributes:
        robot_id      : Unique identifier string for this robot instance.
        linear_speed  : Base linear velocity in m/s.
        angular_speed : Base angular velocity in rad/s.
        is_initialized: Flag indicating successful initialisation.
        pose          : Current robot pose in the world frame.
        path          : Recorded navigation trajectory.
        scan_positions: List of poses where LiDAR scans were triggered.
    """

    # ROS2 topic names (used when running in a real ROS2 environment)
    CMD_VEL_TOPIC   = "/cmd_vel"
    ODOM_TOPIC      = "/odom"
    SCAN_TOPIC      = "/scan"
    PC2_TOPIC       = "/point_cloud2"

    def __init__(
        self,
        robot_id: str = "TB3-01",
        linear_speed: float = 0.2,
        angular_speed: float = 0.5,
    ) -> None:
        """
        Initialise the RobotController with identity and motion parameters.

        Args:
            robot_id      : Human-readable identifier for the robot (default "TB3-01").
            linear_speed  : Forward / backward speed in m/s (default 0.2).
            angular_speed : Rotation speed in rad/s (default 0.5).
        """
        self.robot_id       = robot_id
        self.linear_speed   = linear_speed
        self.angular_speed  = angular_speed
        self.is_initialized = False
        self.pose           = Pose()
        self.path           = NavigationPath()
        self.scan_positions : List[Pose] = []
        self._step_count    = 0          # Internal odometry step counter
        self._emergency_stop= False      # Safety kill-switch flag

        logger.info(
            "RobotController created | robot_id=%s | v=%.2f m/s | ω=%.2f rad/s",
            self.robot_id, self.linear_speed, self.angular_speed,
        )

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def initialize(self) -> bool:
        """
        Perform startup checks and initialise the robot subsystems.

        In a real ROS2 node this would:
          - Call rclpy.init() to start the ROS2 context.
          - Create publishers and subscribers.
          - Wait for the /odom and /scan topics to become available.
          - Request an initial pose estimate from AMCL.

        Returns:
            bool: True if initialisation succeeded, False otherwise.
        """
        logger.info("[%s] Initialising robot subsystems …", self.robot_id)
        time.sleep(0.3)   # Simulates ROS2 startup handshake latency

        # Reset state
        self.pose           = Pose(x=0.0, y=0.0, theta=0.0)
        self.path           = NavigationPath()
        self.scan_positions = []
        self._step_count    = 0
        self._emergency_stop= False
        self.is_initialized = True

        logger.info("[%s] ✓ Robot initialised at %s", self.robot_id, self.pose)
        return True

    def stop(self) -> None:
        """
        Issue a zero-velocity command to bring the robot to a full stop.

        In a real system this publishes Twist(linear.x=0, angular.z=0) to
        /cmd_vel and waits for the robot to decelerate.
        """
        logger.info("[%s] STOP command issued at %s", self.robot_id, self.pose)
        self._emergency_stop = True
        # Simulate deceleration delay
        time.sleep(0.1)

    # ------------------------------------------------------------------
    # Primitive Motion Commands
    # ------------------------------------------------------------------

    def move_forward(self, distance: float = 0.5) -> None:
        """
        Drive the robot straight ahead by the specified distance.

        Kinematics: Δx = distance·cos(θ),  Δy = distance·sin(θ)

        Args:
            distance : Distance to travel in meters (default 0.5 m).
        """
        if not self.is_initialized:
            logger.warning("move_forward called before initialize()!")
            return

        # Simulate travel time proportional to distance (always non-negative)
        travel_time = abs(distance) / max(0.01, self.linear_speed)
        logger.debug(
            "[%s] move_forward | dist=%.2fm | ETA=%.2fs", self.robot_id, distance, travel_time
        )
        time.sleep(max(0.0, travel_time * 0.05))   # Compressed for simulation speed

        # Update pose using dead-reckoning kinematics
        self.pose.x += distance * math.cos(self.pose.theta)
        self.pose.y += distance * math.sin(self.pose.theta)
        self._step_count += 1
        self.path.add(self.pose)

    def turn_left(self, angle_deg: float = 90.0) -> None:
        """
        Rotate the robot counter-clockwise (left) by the given angle.

        Args:
            angle_deg : Rotation amount in degrees (default 90°).
        """
        if not self.is_initialized:
            logger.warning("turn_left called before initialize()!")
            return

        angle_rad   = math.radians(angle_deg)
        rotate_time = abs(angle_rad) / max(0.01, self.angular_speed)
        logger.debug(
            "[%s] turn_left | angle=%.1f° | ETA=%.2fs", self.robot_id, angle_deg, rotate_time
        )
        time.sleep(max(0.0, rotate_time * 0.05))

        self.pose.theta = (self.pose.theta + angle_rad) % (2 * math.pi)
        self.path.add(self.pose)

    def turn_right(self, angle_deg: float = 90.0) -> None:
        """
        Rotate the robot clockwise (right) by the given angle.

        Args:
            angle_deg : Rotation amount in degrees (default 90°).
        """
        if not self.is_initialized:
            logger.warning("turn_right called before initialize()!")
            return

        angle_rad   = math.radians(angle_deg)
        rotate_time = abs(angle_rad) / max(0.01, self.angular_speed)
        logger.debug(
            "[%s] turn_right | angle=%.1f° | ETA=%.2fs", self.robot_id, angle_deg, rotate_time
        )
        time.sleep(max(0.0, rotate_time * 0.05))

        self.pose.theta = (self.pose.theta - angle_rad) % (2 * math.pi)
        self.path.add(self.pose)

    # ------------------------------------------------------------------
    # High-Level Navigation
    # ------------------------------------------------------------------

    def navigate(self, inspection_points: Optional[List[Tuple[float, float]]] = None) -> List[Pose]:
        """
        Execute a pre-planned autonomous inspection sweep inside the shelter.

        The navigation strategy follows a modified wall-following / lawnmower
        pattern designed to maximise sensor coverage of a rectangular room while
        avoiding simulated obstacles (fallen debris).

        In a real system this would call:
            nav2_msgs.action.NavigateToPose via an ActionClient

        Args:
            inspection_points : Optional list of (x, y) waypoints to visit.
                                 If None, a default sweep pattern is generated.

        Returns:
            List[Pose]: The list of scan positions where LiDAR data was captured.
        """
        if not self.is_initialized:
            logger.error("navigate() called before initialize()!")
            return []

        # ---- Build default inspection waypoints if none provided ----
        if inspection_points is None:
            inspection_points = self._generate_inspection_grid(
                room_width=8.0, room_depth=6.0, step=1.5
            )

        logger.info(
            "[%s] Starting autonomous navigation | %d waypoints",
            self.robot_id, len(inspection_points),
        )

        for idx, (wx, wy) in enumerate(inspection_points):
            if self._emergency_stop:
                logger.warning("[%s] Emergency stop triggered — aborting navigation!", self.robot_id)
                break

            logger.info(
                "[%s] → Waypoint %d/%d: (%.2f, %.2f)",
                self.robot_id, idx + 1, len(inspection_points), wx, wy,
            )

            try:
                # Steer towards waypoint
                self._steer_to(wx, wy)

                # Simulate debris avoidance (probabilistic)
                if random.random() < 0.25:
                    self._avoid_obstacle()
            except Exception as exc:
                logger.warning("[%s] Navigation step error at waypoint %d: %s. Continuing path.", self.robot_id, idx + 1, exc)

            # Trigger LiDAR scan at this position
            self.scan_positions.append(Pose(self.pose.x, self.pose.y, self.pose.theta))
            logger.info(
                "[%s] 📡 LiDAR scan triggered at %s", self.robot_id, self.pose
            )

        logger.info(
            "[%s] Navigation complete | total distance=%.2fm | scans=%d",
            self.robot_id, self.path.total_distance(), len(self.scan_positions),
        )
        return self.scan_positions

    # ------------------------------------------------------------------
    # Private Helpers
    # ------------------------------------------------------------------

    def _steer_to(self, target_x: float, target_y: float) -> None:
        """
        Simple proportional steering towards a 2D target waypoint.

        Computes the bearing error between the current heading and the
        direction to the target, then issues turn + forward commands.

        Args:
            target_x : Target X-coordinate.
            target_y : Target Y-coordinate.
        """
        dx    = target_x - self.pose.x
        dy    = target_y - self.pose.y
        dist  = math.sqrt(dx * dx + dy * dy)
        if dist < 0.05:          # Already at target
            return

        # Bearing to target (radians)
        bearing = math.atan2(dy, dx)
        heading_error = bearing - self.pose.theta

        # Normalise to [-π, π]
        heading_error = (heading_error + math.pi) % (2 * math.pi) - math.pi

        # Issue turn command
        if heading_error > 0.1:
            self.turn_left(math.degrees(heading_error))
        elif heading_error < -0.1:
            self.turn_right(math.degrees(-heading_error))

        # Drive forward to target
        self.move_forward(dist)

    def _avoid_obstacle(self) -> None:
        """
        Reactive obstacle avoidance manoeuvre (Bug algorithm inspired).

        When a proximity sensor (or LiDAR returns) detect an obstacle within
        the safe stop distance, the robot backs up slightly, rotates, and
        continues on an alternative heading.
        """
        try:
            logger.debug("[%s] Obstacle detected — executing avoidance manoeuvre", self.robot_id)
            self.move_forward(-0.2)           # Back up 20 cm
            turn_angle = random.choice([45, 60, 90, -45, -60])
            if turn_angle > 0:
                self.turn_left(turn_angle)
            else:
                self.turn_right(-turn_angle)
            self.move_forward(0.3)            # Clear the obstacle
        except Exception as exc:
            logger.warning("[%s] Obstacle avoidance failed gracefully: %s", self.robot_id, exc)

    def _generate_inspection_grid(
        self,
        room_width: float,
        room_depth: float,
        step: float,
    ) -> List[Tuple[float, float]]:
        """
        Generate a lawnmower / boustrophedon inspection grid for a rectangular room.

        This coverage pattern guarantees that every floor tile of the room is
        visited by the robot, maximising LiDAR scan coverage.

        Args:
            room_width : Width of the room in meters (X axis).
            room_depth : Depth of the room in meters (Y axis).
            step       : Grid step size in meters (equal to LiDAR range / 2).

        Returns:
            List[Tuple[float, float]]: Ordered waypoint coordinates.
        """
        waypoints = []
        x = step / 2
        row = 0
        while x < room_width:
            y_range = [step / 2 + j * step for j in range(int(room_depth / step))]
            if row % 2 == 1:
                y_range = list(reversed(y_range))   # Alternate sweep direction
            for y in y_range:
                waypoints.append((x, y))
            x += step
            row += 1
        logger.debug("Generated %d inspection grid waypoints", len(waypoints))
        return waypoints

    # ------------------------------------------------------------------
    # Status / Diagnostics
    # ------------------------------------------------------------------

    def get_status(self) -> dict:
        """
        Return a dictionary containing the current robot status snapshot.

        Returns:
            dict: Status fields including pose, battery estimate, and step count.
        """
        battery_estimate = max(0.0, 100.0 - self._step_count * 0.8)
        return {
            "robot_id"        : self.robot_id,
            "initialized"     : self.is_initialized,
            "pose"            : repr(self.pose),
            "steps"           : self._step_count,
            "distance_m"      : round(self.path.total_distance(), 3),
            "scans_taken"     : len(self.scan_positions),
            "battery_pct"     : round(battery_estimate, 1),
            "emergency_stop"  : self._emergency_stop,
        }
