# System Workflow

## 3D LiDAR-Based Shelter Damage Inspection System

---

## Complete Inspection Workflow

```
┌─────────────────────────────────────────────────────────────────────┐
│                    PHASE 0: DISASTER EVENT                           │
│                                                                       │
│  Natural disaster occurs → Shelter sustains structural damage        │
│  Manual entry is deemed unsafe for rescue personnel                  │
│  Decision made to deploy autonomous robotic inspection               │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    PHASE 1: SYSTEM INITIALISATION                    │
│                                                                       │
│  [RobotController.initialize()]                                       │
│  ● ROS2 node starts; publishes to /cmd_vel, subscribes to /odom     │
│  ● Nav2 lifecycle manager transitions all nodes to ACTIVE state      │
│  ● SLAM toolbox initialises blank map                                │
│  ● Robot pose set to spawn point (1.0, 1.0) in world frame          │
│  ● LiDAR starts spinning; data appears on /velodyne_points          │
│  ● Battery, sensor, and communication checks performed               │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    PHASE 2: AUTONOMOUS NAVIGATION                    │
│                                                                       │
│  [RobotController.navigate()]                                         │
│  ● Boustrophedon (lawnmower) grid computed over shelter area         │
│  ● Nav2 ActionClient sends NavigateToPose goals sequentially         │
│  ● Robot drives toward each waypoint; SLAM updates the map           │
│  ● Reactive obstacle avoidance (VFH+ / DWA planner) active          │
│  ● At each waypoint: record pose → trigger LiDAR scan               │
│  ● Safety: battery monitoring; auto-return if < 20%                 │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    PHASE 3: LiDAR DATA ACQUISITION                   │
│                                                                       │
│  [LiDARProcessor.generate_scan() + filter_scan()]                    │
│  ● Velodyne VLP-16 captures full 360° × 16-channel scan             │
│  ● 1,800 rays per channel × 16 channels = 28,800 pts per scan       │
│  ● At 10 Hz: ~288,000 pts/sec (sim: compressed timing)              │
│  ● Gaussian noise (σ=3 cm) added per datasheet                      │
│  ● 2% per-ray dropout for specular/out-of-range returns             │
│  ● Statistical Outlier Removal (5-ray sliding window, 3σ reject)    │
│  ● Damage zones alter returns: missing wall → long range             │
│    roof hole → inf return, debris → short noisy return              │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│              PHASE 4: POINT CLOUD GENERATION                         │
│                                                                       │
│  [PointCloudGenerator.scan_to_pointcloud() + accumulate()]          │
│  ● Spherical → Cartesian conversion for all valid rays:             │
│      x = r·cos(elev)·cos(az + θ_robot) + rx                        │
│      y = r·cos(elev)·sin(az + θ_robot) + ry                        │
│      z = r·sin(elev) + sensor_height                                │
│  ● All clouds transformed to world frame via robot pose             │
│  ● Sequential clouds merged into accumulated map                    │
│  ● Voxel grid down-sampling (5 cm voxels) reduces density           │
│  ● Height-based colour mapping for visualisation (viridis)          │
│  ● 3D scatter plot (Matplotlib) + top-view projection               │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│              PHASE 5: 3D ENVIRONMENT RECONSTRUCTION                  │
│                                                                       │
│  [EnvironmentMapper.build_occupancy_grid() + classify_regions()]    │
│  ● Points projected onto 10 cm resolution 2D occupancy grid         │
│  ● Height segmentation:                                              │
│      z < 0.15 m  → FLOOR (FREE cells)                               │
│      z = 0.15–2.8 m → WALL (OCCUPIED cells)                         │
│      z > 2.8 m   → CEILING region                                   │
│  ● Quadrant-based wall labelling: North/South/East/West             │
│  ● 2D DSM (Digital Surface Model) height map computed               │
│  ● Floor plan visualised as occupancy grid image                    │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│              PHASE 6: STRUCTURAL DAMAGE DETECTION                    │
│                                                                       │
│  [DamageDetector.detect()]                                            │
│                                                                       │
│  Algorithm 1: MISSING WALL                                           │
│    • Scan perimeter cells of occupancy grid                          │
│    • Find runs of ≥5 consecutive FREE cells                          │
│    • Flag as missing wall section with extent                        │
│                                                                       │
│  Algorithm 2: BROKEN ROOF                                            │
│    • Extract ceiling-height band from height map                    │
│    • Compute 3×3 neighbourhood mean                                  │
│    • Flag cells with > 0.5 m drop vs. neighbourhood                 │
│                                                                       │
│  Algorithm 3: LARGE HOLES / VOIDS                                    │
│    • Flood-fill over UNKNOWN cells bordering FREE cells              │
│    • Clusters ≥ 8 cells flagged as floor void                       │
│                                                                       │
│  Algorithm 4: COLLAPSED SECTION                                      │
│    • Process debris region from mapper                               │
│    • DBSCAN-like radius clustering (ε=0.6m, min_pts=5)             │
│    • Clusters at wall-height band → collapsed section               │
│                                                                       │
│  Algorithm 5: LEANING WALL                                           │
│    • SVD/PCA on wall region points                                   │
│    • Extract plane normal (smallest singular value)                  │
│    • Z-component > 0.25 → flagged as leaning                        │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│              PHASE 7: SEVERITY CLASSIFICATION                        │
│                                                                       │
│  [SeverityClassifier.classify()]                                     │
│  ● Multi-factor additive scoring model (0–100):                     │
│      Factor 1: Type weights (Collapsed=30, Missing Wall=22, ...)    │
│      Factor 2: Extent penalty (log-scaled, max 15 pts)              │
│      Factor 3: Count multiplier (multiple damage types)             │
│      Factor 4: Coverage uncertainty (unscanned areas)               │
│      Factor 5: Confidence adjustment (low-conf detections)          │
│                                                                       │
│  ● Risk mapping:                                                     │
│      0–15  : SAFE     (green)                                        │
│      16–35 : LOW      (yellow)                                       │
│      36–55 : MEDIUM   (orange)                                       │
│      56–75 : HIGH     (red)                                          │
│      76–100: CRITICAL (dark red)                                     │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│              PHASE 8: REPORT GENERATION                              │
│                                                                       │
│  [ReportGenerator.generate()]                                         │
│  ● Professional inspection report compiled:                          │
│      § 1: Cover / Header                                             │
│      § 2: Mission Overview                                           │
│      § 3: Robot & Sensor Specifications                              │
│      § 4: Scan Quality Statistics                                    │
│      § 5: Damage Inventory (tabulated)                               │
│      § 6: Severity Assessment                                        │
│      § 7: Recommendations                                            │
│      Appendix: Full damage descriptions + evidence points            │
│  ● Saved to reports/inspection_report.txt                           │
│  ● ANSI-coloured version displayed in terminal                       │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│              PHASE 9: ROBOT STOP & MISSION COMPLETE                  │
│                                                                       │
│  ● Robot navigates back to home position                             │
│  ● /cmd_vel publishes zero velocity                                  │
│  ● Nav2 transitions to INACTIVE state                                │
│  ● Final summary printed to console                                  │
│  ● Log file flushed and closed                                       │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Decision Points

| Condition | Action |
|-----------|--------|
| Battery < 20% | Abort inspection, return to base |
| Emergency stop triggered | Publish zero velocity, halt pipeline |
| No valid LiDAR returns | Log warning, continue with partial data |
| Obstacle within 0.3 m | Execute reactive avoidance manoeuvre |
| Score > 75 | Immediately flag CRITICAL, stop robot |

---

*Last updated: July 2025 | Team LiDAR-Inspect*
