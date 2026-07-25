# System Architecture

## 3D LiDAR-Based Shelter Damage Inspection System

---

## Overview

This document describes the complete system architecture of the 3D LiDAR-Based Shelter Damage Inspection System. The architecture follows ROS2 design principles, separating concerns into dedicated nodes that communicate over topics and services.

---

## High-Level Architecture

```
┌──────────────────────────────────────────────────────────────────────────┐
│                    DISASTER RESPONSE COMMAND CENTRE                       │
│                    (Remote Monitoring Interface)                           │
└────────────────────────────┬─────────────────────────────────────────────┘
                             │ SSH / ROS2 Bridge / Web Dashboard
                             ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                    TURTLEBOT3 ONBOARD COMPUTER                            │
│                    (Raspberry Pi 4B — Ubuntu 22.04 + ROS2 Humble)        │
│                                                                            │
│  ┌─────────────────┐   ┌──────────────────┐   ┌─────────────────────┐   │
│  │ robot_controller│──▶│  lidar_processor │──▶│ pointcloud_generator│   │
│  │  (Navigation)   │   │  (Scan Capture)  │   │ (3D Reconstruction) │   │
│  └────────┬────────┘   └────────┬─────────┘   └──────────┬──────────┘   │
│           │                     │                          │              │
│           ▼                     ▼                          ▼              │
│  ┌─────────────────────────────────────────────────────────────────┐     │
│  │               environment_mapper (3D Map Builder)                │     │
│  │     Occupancy Grid │ Height Map │ Structural Region Segmentation │     │
│  └──────────────────────────────┬──────────────────────────────────┘     │
│                                  │                                        │
│                                  ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────┐     │
│  │               damage_detector (Multi-Algorithm Pipeline)         │     │
│  │  Missing Wall │ Broken Roof │ Large Holes │ Collapse │ Lean      │     │
│  └──────────────────────────────┬──────────────────────────────────┘     │
│                                  │                                        │
│                                  ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────┐     │
│  │              severity_classifier (Risk Score Engine)             │     │
│  │     0–15: SAFE │ 16–35: LOW │ 36–55: MEDIUM │ 56+: HIGH/CRIT   │     │
│  └──────────────────────────────┬──────────────────────────────────┘     │
│                                  │                                        │
│                                  ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────┐     │
│  │              report_generator (Output Layer)                     │     │
│  │     TXT Report │ Terminal Display │ (Future: PDF / GIS / Web)   │     │
│  └─────────────────────────────────────────────────────────────────┘     │
│                                                                            │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## ROS2 Node Graph

```
/velodyne_driver ──────────▶ /velodyne_points (PointCloud2)
                                      │
                                      ▼
/slam_toolbox ◀────────── /scan (LaserScan) ◀──── /velodyne_convert
      │
      ▼
/map (OccupancyGrid)
            \
             ▼
           /nav2_bt_navigator ◀──── /robot_controller
                   │
                   ▼
           /cmd_vel (Twist) ──▶ /turtlebot3_diff_drive
                                         │
                                         ▼
                                 /odom (Odometry)
                                         │
                                   /tf tree update

/shelter_inspection_node ──────────────────────────────────────▶
    Subscribes: /velodyne_points, /map, /odom
    Publishes : /damage_markers (MarkerArray), /inspection/severity (Float32)
```

---

## Data Flow Architecture

```
SENSOR LAYER
    Velodyne VLP-16
    └── Raw UDP packets (pcap stream)
        └── /velodyne_driver node
            └── sensor_msgs/PointCloud2 → /velodyne_points

PROCESSING LAYER
    /velodyne_points
        └── LiDARProcessor
            ├── Ray casting simulation
            ├── Gaussian noise application
            ├── Statistical outlier removal
            └── MultiLayerScan output

    MultiLayerScan
        └── PointCloudGenerator
            ├── Spherical → Cartesian transform
            ├── World frame transform (robot pose)
            ├── Voxel grid down-sampling
            └── Accumulated PointCloud output

    PointCloud
        └── EnvironmentMapper
            ├── Occupancy Grid (2D floor plan)
            ├── Height Map (DSM elevation model)
            └── Structural Region Segmentation

ANALYSIS LAYER
    ShelterMap
        └── DamageDetector
            ├── Missing Wall Detection (perimeter gap analysis)
            ├── Broken Roof Detection (height map drop analysis)
            ├── Large Hole Detection (connected components)
            ├── Collapsed Section Detection (DBSCAN clustering)
            └── Leaning Wall Detection (SVD plane fitting)

    DamageReport
        └── SeverityClassifier
            ├── Type weight scoring
            ├── Extent penalty
            ├── Count multiplier
            ├── Coverage uncertainty
            └── SeverityResult (score + risk level)

OUTPUT LAYER
    SeverityResult + DamageReport
        └── ReportGenerator
            ├── Plain-text report (inspection_report.txt)
            ├── Terminal display (ANSI coloured)
            └── RViz2 marker array (/damage_markers)
```

---

## Technology Stack Mapping

| Layer | Component | Technology |
|-------|-----------|------------|
| Simulation | World model | Gazebo + SDF |
| Robot Platform | Physical base | TurtleBot3 Burger |
| Sensor | LiDAR | Velodyne VLP-16 |
| Middleware | Communication | ROS2 Humble |
| Navigation | Path planning | Navigation2 (Nav2) |
| SLAM | Mapping | slam_toolbox |
| 3D Processing | Point cloud | Open3D + NumPy |
| Computer Vision | Grid analysis | OpenCV |
| Visualisation | 3D / 2D plots | Matplotlib + RViz2 |
| Intelligence | Damage detection | Custom algorithms |
| Classification | Risk scoring | Multi-factor model |
| Reporting | Output | Python + PDF |

---

## Key Design Decisions

### 1. Modular Pipeline
Each phase of the inspection pipeline is implemented as an independent class, allowing:
- Independent unit testing of each module
- Easy replacement of algorithms (e.g., swap DBSCAN for Euclidean clustering)
- Parallel development across team members

### 2. ROS2-Compatible Data Structures
All data classes mirror ROS2 message types (LaserScan, PointCloud2, OccupancyGrid) so that the simulation code can be connected to a real robot with minimal refactoring.

### 3. Transparent Scoring
The severity classifier uses an additive, rule-based model rather than a black-box ML model. This ensures full auditability — critical for emergency management decisions.

### 4. Safety-First Defaults
When data is absent or uncertain, the system defaults to the most cautious (higher severity) interpretation, following fail-safe engineering principles.

---

*Last updated: July 2025 | Team LiDAR-Inspect*
