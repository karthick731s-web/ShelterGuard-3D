# System Design Document

## 3D LiDAR-Based Shelter Damage Inspection System

**Version:** 1.0.0  
**Date:** July 2025  
**Authors:** Team LiDAR-Inspect  
**Status:** Prototype / Hackathon Demo

---

## 1. Problem Statement

Natural disasters including earthquakes, cyclones, floods, and landslides cause severe structural damage to shelters and buildings. Current post-disaster structural inspection workflows require human inspectors to physically enter damaged structures — a process that:

- **Endangers rescue personnel** (structural collapse risk)
- **Delays rescue operations** (inspection queues)
- **Produces inconsistent results** (human error, fatigue)
- **Cannot operate at scale** (limited inspector capacity)

**Our Solution:** An autonomous robotic inspection system that enters the damaged shelter in place of human inspectors, performs a complete 3D LiDAR scan, detects structural anomalies, and generates a standardised risk assessment report.

---

## 2. Objectives

| Priority | Objective |
|----------|-----------|
| P0 | Detect at least 4 categories of structural damage from LiDAR data |
| P0 | Produce a severity score (0–100) and risk level category |
| P0 | Generate a machine-readable inspection report |
| P1 | Autonomous navigation without human teleoperation |
| P1 | Operate under simulated sensor noise and scan gaps |
| P2 | Compatible with a real TurtleBot3 + Velodyne VLP-16 deployment |
| P2 | Extendable to multi-robot inspection teams |

---

## 3. Design Constraints

| Constraint | Specification |
|------------|---------------|
| Robot platform | TurtleBot3 Burger (ROBOTIS) |
| Sensor | Velodyne VLP-16 (simulated) |
| Middleware | ROS2 Humble (Python) |
| Simulation | Gazebo Classic 11 |
| Language | Python 3.10+ |
| Environment | Indoor shelter, 8 m × 6 m × 3 m |
| Max speed | 0.22 m/s (TurtleBot3 rated) |
| Scan rate | 10 Hz (VLP-16 rated) |
| Battery | ~90 min (TurtleBot3 rated) |

---

## 4. Module Design

### 4.1 RobotController

**Design Pattern:** Command / Controller  
**Interface:** ROS2 action client wrapping Nav2 `NavigateToPose`

```
RobotController
├── initialize()        → Set up ROS2 node, verify topics alive
├── navigate()          → Execute boustrophedon sweep
├── move_forward(dist)  → Publish linear velocity command
├── turn_left(deg)      → Publish angular velocity command
├── turn_right(deg)     → Publish angular velocity command (negative)
├── stop()              → Publish zero velocity
├── _steer_to(x, y)     → Proportional heading controller
├── _avoid_obstacle()   → Bug algorithm reactive avoidance
├── _generate_grid()    → Boustrophedon waypoint generator
└── get_status()        → Telemetry snapshot
```

**Key Design Choice:** The navigation grid is computed from room geometry rather than hardcoded, allowing the system to adapt to different shelter sizes without code changes.

---

### 4.2 LiDARProcessor

**Design Pattern:** Factory + Strategy  
**Interface:** Subscribes `/velodyne_points`, exposes typed scan objects

```
LiDARProcessor
├── generate_scan(x, y, θ)  → Ray-cast all 16 channels
├── filter_scan(scan)        → Median filter all layers
├── get_scan_statistics()    → Quality metrics
├── _cast_layer(...)         → Single elevation layer ray caster
├── _ray_aabb_intersect()    → AABB wall intersection
├── _apply_damage_zones()    → Damage zone return modifiers
├── _compute_intensity()     → 1/r² intensity model
└── _median_filter()         → Sliding window median
```

**Key Design Choice:** Damage zones are defined as data (in `shelter_profile` dict), not as code conditionals, making the simulation trivially extensible to new damage types.

---

### 4.3 PointCloudGenerator

**Design Pattern:** Builder + Accumulator  
**Interface:** Consumes `MultiLayerScan`, produces `PointCloud`

```
PointCloudGenerator
├── scan_to_pointcloud(scan)  → Spherical → Cartesian conversion
├── accumulate(cloud)          → Merge into running map
├── downsample(voxel_size)     → Voxel grid reduction
├── get_accumulated_cloud()    → Return merged cloud
├── visualize_3d(...)          → Matplotlib 3D scatter
├── visualize_top_view(...)    → 2D top-down projection
└── _colorize(pts, intensities) → Height-mapped colouring
```

---

### 4.4 EnvironmentMapper

**Design Pattern:** Builder + Visitor  
**Interface:** Consumes `PointCloud`, produces `ShelterMap`

```
EnvironmentMapper
├── accumulate_cloud(cloud)    → Merge cloud data
├── build_occupancy_grid()     → Project to 2D grid
├── classify_regions()         → Height-band segmentation
├── compute_height_map()       → DSM elevation model
├── get_map()                  → Return ShelterMap
├── visualize_occupancy_grid() → Floor plan visualisation
└── visualize_height_map()     → Elevation visualisation
```

---

### 4.5 DamageDetector

**Design Pattern:** Strategy (pluggable algorithm pipeline)  
**Interface:** Consumes `ShelterMap`, produces `DamageReport`

Each detection algorithm is an independent private method, making it easy to:
- Enable/disable individual algorithms
- Add new detection types without touching existing code
- Unit test algorithms in isolation

```
DamageDetector
├── detect()                    → Run full pipeline, return DamageReport
├── _detect_missing_walls()     → Perimeter gap scan
├── _detect_broken_roof()       → Height drop analysis
├── _detect_large_holes()       → Flood-fill void detection
├── _detect_collapsed_sections()→ DBSCAN debris clustering
├── _detect_leaning_walls()     → SVD plane fitting
└── _simple_cluster(pts, r)     → Greedy radius clustering
```

---

### 4.6 SeverityClassifier

**Design Pattern:** Scoring Engine  
**Interface:** Consumes `DamageReport`, produces `SeverityResult`

**Scoring Formula:**
```
score = Σ(type_weights) + log(total_extent)×5 + (n-1)×2.5 + uncov_penalty + conf_adj
score = clamp(score, 0, 100)
```

**Risk Level Mapping (FEMA P-154 inspired):**
```
0–15  : SAFE
16–35 : LOW
36–55 : MEDIUM
56–75 : HIGH
76–100: CRITICAL
```

---

### 4.7 ReportGenerator

**Design Pattern:** Template Method  
**Interface:** Consumes all pipeline outputs, produces formatted text

```
ReportGenerator
├── generate(output_path)          → Assemble + save report
├── display(content)               → Print to stdout
├── _build_report()                → Concatenate all sections
├── _section_header()              → Cover page
├── _section_mission_overview()    → Mission metadata
├── _section_robot_details()       → Robot + sensor specs
├── _section_scan_statistics()     → LiDAR quality metrics
├── _section_damage_inventory()    → Tabulated damage list
├── _section_severity_assessment() → Score + risk level
├── _section_recommendations()     → Actionable guidance
├── _section_appendix()            → Raw damage descriptions
├── _section_footer()              → Legal disclaimer
└── _strip_ansi(text)             → Clean text for file output
```

---

## 5. Data Flow Contracts

### Input/Output Types

| Module | Input | Output |
|--------|-------|--------|
| RobotController | None | `List[Pose]` scan positions |
| LiDARProcessor | `(x, y, θ)` pose | `MultiLayerScan` |
| PointCloudGenerator | `MultiLayerScan` | `PointCloud` |
| EnvironmentMapper | `PointCloud` | `ShelterMap` |
| DamageDetector | `ShelterMap` | `DamageReport` |
| SeverityClassifier | `DamageReport` | `SeverityResult` |
| ReportGenerator | All above | Report string + `.txt` file |

---

## 6. Error Handling Strategy

| Error Type | Response |
|------------|----------|
| Empty point cloud | Log WARNING, continue with partial data |
| Nav2 goal failure | Retry once, then skip waypoint |
| Sensor dropout > 10% | Log WARNING in report, increase uncertainty |
| Scipy/numpy exception | Log ERROR, return safe default |
| File write failure | Log ERROR, dump report to stdout |
| KeyboardInterrupt | Graceful robot stop, then exit |

---

## 7. Scalability Considerations

| Aspect | Current (Prototype) | Future (Production) |
|--------|---------------------|---------------------|
| Robots | 1 TurtleBot3 | Multi-robot fleet (ROS2 multi-agent) |
| Communication | Local ROS2 | 5G / mesh radio bridge |
| Mapping | In-memory | Persistent OctoMap database |
| Detection | Rule-based | ML (PointNet++ / 3D CNN) |
| Reporting | TXT file | REST API + GIS KML export |
| Speed | Real-time sim | Embedded GPU (NVIDIA Jetson) |

---

*Last updated: July 2025 | Team LiDAR-Inspect*
