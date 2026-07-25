"""
inspection.launch.py
=====================
ROS2 Launch file for the 3D LiDAR-Based Shelter Damage Inspection System.

This launch file starts the following nodes simultaneously:
    1. Gazebo Simulator     → Loads the damaged shelter world
    2. TurtleBot3 Spawn Node→ Spawns the robot in Gazebo
    3. LiDAR Publisher Node → Publishes sensor_msgs/PointCloud2 on /scan
    4. Nav2 Stack           → Navigation2 lifecycle manager + BT navigator
    5. RViz2                → Visualisation with custom config
    6. Inspection Node      → Main inspection pipeline node

Usage (ROS2 Humble):
    ros2 launch shelter_inspection inspection.launch.py

Environment Variables (must be set before launching):
    TURTLEBOT3_MODEL=burger
    GAZEBO_MODEL_PATH=/path/to/gazebo_world

Author  : Team LiDAR-Inspect
Project : 3D LiDAR-Based Shelter Damage Inspection System
License : MIT
"""

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    IncludeLaunchDescription,
    ExecuteProcess,
    TimerAction,
    LogInfo,
)
from launch.conditions import IfCondition, UnlessCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import (
    LaunchConfiguration,
    PathJoinSubstitution,
    EnvironmentVariable,
)
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description() -> LaunchDescription:
    """
    Generate the complete ROS2 LaunchDescription for the inspection system.

    Returns:
        LaunchDescription: All launch actions and node configurations.
    """

    # -----------------------------------------------------------------------
    # Package / directory paths
    # -----------------------------------------------------------------------
    pkg_shelter = FindPackageShare("shelter_inspection")
    pkg_nav2    = FindPackageShare("nav2_bringup")
    pkg_tb3_gz  = FindPackageShare("turtlebot3_gazebo")

    # World file path (relative to workspace root)
    world_file  = PathJoinSubstitution([
        FindPackageShare("shelter_inspection"),
        "../../..",           # Navigate up to project root
        "gazebo_world",
        "damaged_shelter.sdf",
    ])

    # Nav2 parameter file
    nav2_params = PathJoinSubstitution([pkg_shelter, "config", "nav2_params.yaml"])

    # RViz2 config
    rviz_config = PathJoinSubstitution([pkg_shelter, "config", "inspection.rviz"])

    # -----------------------------------------------------------------------
    # Launch Arguments (configurable from command line)
    # -----------------------------------------------------------------------
    declare_shelter_id = DeclareLaunchArgument(
        "shelter_id",
        default_value  = "SH-001",
        description    = "Unique identifier for the shelter being inspected",
    )
    declare_robot_id = DeclareLaunchArgument(
        "robot_id",
        default_value  = "TB3-01",
        description    = "Robot identifier for logging and reports",
    )
    declare_use_rviz = DeclareLaunchArgument(
        "use_rviz",
        default_value  = "true",
        description    = "Launch RViz2 visualiser (true/false)",
    )
    declare_use_sim_time = DeclareLaunchArgument(
        "use_sim_time",
        default_value  = "true",
        description    = "Use Gazebo simulation time (true for sim, false for real robot)",
    )
    declare_num_scans = DeclareLaunchArgument(
        "num_scans",
        default_value  = "8",
        description    = "Number of LiDAR scan passes to perform",
    )

    # -----------------------------------------------------------------------
    # Action 1: Gazebo Simulator (loads damaged shelter world)
    # -----------------------------------------------------------------------
    gazebo = ExecuteProcess(
        cmd  = [
            "gazebo",
            "--verbose",
            world_file,
            "-s", "libgazebo_ros_init.so",           # ROS2 system plugin
            "-s", "libgazebo_ros_factory.so",         # Entity spawn plugin
        ],
        output = "screen",
        name   = "gazebo_simulator",
    )

    # -----------------------------------------------------------------------
    # Action 2: Robot State Publisher (broadcasts TurtleBot3 URDF transforms)
    # -----------------------------------------------------------------------
    robot_state_publisher = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            PathJoinSubstitution([pkg_tb3_gz, "launch", "spawn_turtlebot3.launch.py"])
        ]),
        launch_arguments = {
            "x_pose"       : "1.0",
            "y_pose"       : "1.0",
            "z_pose"       : "0.01",
            "use_sim_time" : LaunchConfiguration("use_sim_time"),
        }.items(),
    )

    # -----------------------------------------------------------------------
    # Action 3: Navigation2 Stack
    # -----------------------------------------------------------------------
    nav2_bringup = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            PathJoinSubstitution([pkg_nav2, "launch", "navigation_launch.py"])
        ]),
        launch_arguments = {
            "use_sim_time" : LaunchConfiguration("use_sim_time"),
            "params_file"  : nav2_params,
        }.items(),
    )

    # -----------------------------------------------------------------------
    # Action 4: RViz2 (optional, gated by use_rviz argument)
    # -----------------------------------------------------------------------
    rviz2_node = Node(
        package         = "rviz2",
        executable      = "rviz2",
        name            = "rviz2",
        arguments       = ["-d", rviz_config],
        parameters      = [{"use_sim_time": LaunchConfiguration("use_sim_time")}],
        condition       = IfCondition(LaunchConfiguration("use_rviz")),
        output          = "screen",
    )

    # -----------------------------------------------------------------------
    # Action 5: Main Inspection Pipeline Node
    # -----------------------------------------------------------------------
    inspection_node = Node(
        package    = "shelter_inspection",
        executable = "main",
        name       = "shelter_inspection_node",
        output     = "screen",
        parameters = [
            {"shelter_id"  : LaunchConfiguration("shelter_id")},
            {"robot_id"    : LaunchConfiguration("robot_id")},
            {"num_scans"   : LaunchConfiguration("num_scans")},
            {"use_sim_time": LaunchConfiguration("use_sim_time")},
        ],
        # Remap default topics to match the TurtleBot3 + Velodyne naming
        remappings = [
            ("/scan",             "/velodyne_scan"),
            ("/cmd_vel",          "/cmd_vel"),
            ("/odom",             "/odom"),
            ("/point_cloud2",     "/velodyne_points"),
        ],
    )

    # -----------------------------------------------------------------------
    # Action 6: Delay inspection start until Gazebo and Nav2 are ready
    # -----------------------------------------------------------------------
    delayed_inspection = TimerAction(
        period  = 8.0,   # Wait 8 seconds for Gazebo + Nav2 to fully initialise
        actions = [
            LogInfo(msg="[shelter_inspection] Starting inspection pipeline …"),
            inspection_node,
        ],
    )

    # -----------------------------------------------------------------------
    # Assemble LaunchDescription
    # -----------------------------------------------------------------------
    return LaunchDescription([
        # Launch arguments
        declare_shelter_id,
        declare_robot_id,
        declare_use_rviz,
        declare_use_sim_time,
        declare_num_scans,

        # Simulation environment
        gazebo,
        robot_state_publisher,

        # Navigation stack
        nav2_bringup,

        # Visualisation
        rviz2_node,

        # Inspection (delayed start)
        delayed_inspection,

        # Info log
        LogInfo(msg="[shelter_inspection] Launch file loaded. Gazebo starting …"),
    ])
