# Visual-Enhanced Robot Navigation

**Autonomous ground vehicle navigation stack with aerial RGBD obstacle perception**  
ROS 2 Jazzy · Gazebo Sim · TurtleBot3 Burger

---

## Overview

This repository implements a complete autonomous navigation stack for a differential-drive mobile robot operating in a simulated warehouse environment. The central contribution is an **aerially-mounted RGBD depth camera** that detects obstacles invisible to the robot's floor-level LiDAR — such as objects on shelves, overhanging structures, or raised platforms — and feeds that data directly into the Nav2 local costmap.

The stack is built on top of ROS 2 standard packages (Nav2, SLAM Toolbox, robot_localization) but extends them with original configuration, sensor integration, and a modular launch architecture not found in any official tutorial.

---

## Repository Structure

```
Visual-enhanced-robot-nav/
├── tb3_description/              # Robot description package
│   ├── CMakeLists.txt
│   ├── package.xml
│   ├── meshes/                   # TB3 Burger mesh files
│   ├── rviz/
│   │   └── model_house.rviz      # Pre-configured RViz2 layout
│   └── urdf/
│       └── burger_tb3/
│           └── robot_define.urdf.xacro   # TB3 Burger URDF with aerial camera link
│
└── vision_bot/                   # Main navigation package
    ├── CMakeLists.txt
    ├── package.xml
    ├── launch/
    │   ├── world_launch.py               # Phase 1: Gazebo world + robot spawn
    │   ├── agv_map_launch.py             # Phase 2: SLAM mapping
    │   ├── agv_localise_launch.py        # Phase 3: Localization on saved map
    │   ├── agv_nav_launch.py             # Phase 4: Nav2 navigation stack
    │   └── navigation.launch.py          # Nav2 bringup (called by agv_nav_launch)
    ├── config/
    │   ├── gz_bridge.yaml                # Gazebo↔ROS 2 topic bridge (13 topics)
    │   ├── ekf.yaml                      # EKF sensor fusion (odom + IMU)
    │   ├── nav2_params.yaml              # Full Nav2 parameter file
    │   ├── mapper_params_online_async.yaml    # SLAM Toolbox mapping config
    │   └── mapper_params_localization.yaml    # SLAM Toolbox localization config
    ├── worlds/
    │   └── my_world.sdf                  # Gazebo warehouse simulation world
    └── maps/
        ├── my_world_map.yaml             # Occupancy grid (for Nav2 map_server)
        ├── my_world_map.pgm              # Occupancy grid image
        └── my_world_map_serialize        # Serialized SLAM map (for localization mode)
```

---

## System Architecture

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                            GAZEBO SIM (my_world.sdf)                        ║
║                                                                              ║
║   ┌─────────────────────┐          ┌──────────────────────────────────────┐ ║
║   │   TurtleBot3 Burger  │          │      Aerial RGBD Camera (static)     │ ║
║   │  ├─ LiDAR            │          │  ├─ /aerial_rgbd_camera/image        │ ║
║   │  ├─ Wheel Encoders   │          │  ├─ /aerial_rgbd_camera/depth_image  │ ║
║   │  └─ IMU              │          │  └─ /aerial_rgbd_camera/points       │ ║
║   └──────────┬──────────┘          └──────────────────┬───────────────────┘ ║
║              │ /scan  /odom  /imu/data  /tf             │ PointCloud2         ║
╚══════════════╪═════════════════════════════════════════╪════════════════════╝
               │                                         │
               └──────────────┬──────────────────────────┘
                               │  ros_gz_bridge  (gz_bridge.yaml)
                               ▼
╔══════════════════════════════════════════════════════════════════════════════╗
║                               ROS 2 LAYER                                   ║
║                                                                              ║
║  ┌────────────────────────┐    ┌───────────────────────────────────────────┐║
║  │  robot_state_publisher  │    │          robot_localization EKF           │║
║  │  (URDF xacro → /tf)     │    │  odom0: /odom    → vx, vyaw (vel only)   │║
║  └────────────────────────┘    │  imu0:  /imu/data → yaw, vyaw             │║
║                                 │  publishes: odom → base_footprint TF      │║
║  ┌────────────────────────┐    └───────────────────┬───────────────────────┘║
║  │  static_tf_publisher    │                        │                        ║
║  │  aerial_cam/link →      │    ┌───────────────────▼───────────────────────┐║
║  │  optical_frame (RPY)    │    │             slam_toolbox                  │║
║  └────────────────────────┘    │  mapping mode:  builds /map from /scan    │║
║                                 │  localize mode: loads serialized map      │║
║                                 │  publishes: map → odom TF                 │║
║                                 └───────────────────┬───────────────────────┘║
║                                                      │                        ║
║  ┌───────────────────────────────────────────────────▼───────────────────────┐║
║  │                            Nav2 Stack                                      │║
║  │                                                                             │║
║  │  ┌──────────────────────────────┐   ┌──────────────────────────────────┐  │║
║  │  │       Global Costmap          │   │         Local Costmap            │  │║
║  │  │  static_layer   (/map)        │   │  voxel_layer ◄─ /scan (clear+mark)│ │║
║  │  │  obstacle_layer (/scan)       │   │  voxel_layer ◄─ /aerial_rgbd/    │  │║
║  │  │  inflation_layer (r=0.70m)    │   │               points (mark only)  │  │║
║  │  └──────────────┬───────────────┘   └──────────────┬───────────────────┘  │║
║  │                 │                                   │                       │║
║  │  ┌──────────────▼───────────────────────────────────▼──────────────────┐  │║
║  │  │  planner_server (NavFn/A*) → bt_navigator → controller_server (MPPI)│  │║
║  │  └────────────────────────────────────────────────────────────────────┬┘  │║
║  │                                                                        │   │║
║  │              velocity_smoother → collision_monitor → cmd_vel ──────────┘   │║
║  └─────────────────────────────────────────────────────────────────────────────┘║
╚══════════════════════════════════════════════════════════════════════════════════╝
               │ cmd_vel (geometry_msgs/Twist)
               ▼
        ros_gz_bridge → Gazebo robot actuators
```

---

## Prerequisites

### System Requirements

| Dependency | Version |
|-----------|---------|
| Ubuntu | 24.04 LTS |
| ROS 2 | Jazzy Jalisco |
| Gazebo | Harmonic |
| Python | 3.12+ |

### ROS 2 Packages

```bash
sudo apt install -y \
  ros-jazzy-nav2-bringup \
  ros-jazzy-nav2-msgs \
  ros-jazzy-slam-toolbox \
  ros-jazzy-robot-localization \
  ros-jazzy-ros-gz-bridge \
  ros-jazzy-ros-gz-sim \
  ros-jazzy-robot-state-publisher \
  ros-jazzy-tf2-ros \
  ros-jazzy-rviz2 \
  ros-jazzy-xacro \
  ros-jazzy-nav2-mppi-controller \
  ros-jazzy-opennav-docking
```

---

## Installation

```bash
# Create workspace
mkdir -p ~/vision_nav/src
cd ~/vision_nav/src

# Clone repository
git clone https://github.com/bineeshajabi/Visual-enhanced-robot-nav.git .

# Install dependencies
cd ~/vision_nav
rosdep install --from-paths src --ignore-src -r -y

# Build
colcon build --symlink-install

# Source
source install/setup.bash
```

---

## Usage — Four-Phase Launch Sequence

The stack is split into four independent launch files. Each can be restarted without affecting the others, which mirrors real AGV deployment workflows.

### Phase 1 — World + Robot Spawn

Starts Gazebo Sim, spawns the TB3 Burger, launches the GZ↔ROS2 bridge, and publishes the robot URDF and static camera TF.

```bash
ros2 launch vision_bot world_launch.py
```

**Optional pose arguments:**
```bash
ros2 launch vision_bot world_launch.py x:=1.0 y:=2.0 Y:=1.57
```

**What this launches:**
- Gazebo Sim with `my_world.sdf`
- `robot_state_publisher` with TB3 Burger URDF
- `ros_gz_bridge` (13 topics — see `gz_bridge.yaml`)
- Static TF: `aerial_rgbd_camera/link` → `aerial_rgbd_camera_optical_frame`

---

### Phase 2 — SLAM Mapping

Runs SLAM Toolbox in online async mode. Drive the robot manually to build the environment map.

```bash
ros2 launch vision_bot agv_map_launch.py
```

**Saving the map:**
```bash
# Standard occupancy grid (for Nav2 map_server)
ros2 run nav2_map_server map_saver_cli -f ~/vision_nav/src/vision_bot/maps/my_world_map

# Serialized map (for slam_toolbox localization mode)
# Use the SLAM Toolbox panel in RViz2 → "Serialize Map"
# Save to: vision_bot/maps/my_world_map_serialize
```

> **Note:** Both the `.yaml/.pgm` occupancy grid and the serialized SLAM map are needed. The occupancy grid is used by Nav2's `map_server`; the serialized map is loaded by SLAM Toolbox in localization mode.

---

### Phase 3 — Localization

Loads the saved serialized map and runs SLAM Toolbox in localization mode. The robot localizes against the known map without re-mapping.

```bash
ros2 launch vision_bot agv_localise_launch.py
```

**What this launches:**
- `slam_toolbox` in `localization` mode loading `my_world_map_serialize`
- Static TF: `map` → `aerial_rgbd_camera/link` (calibrated from map-building session)
- RViz2 with pre-configured layout

> **If relocalization fails:** Use the RViz2 "2D Pose Estimate" tool to manually set the initial pose. SLAM Toolbox will correct from there using scan matching.

---

### Phase 4 — Navigation

Launches the full Nav2 stack.

```bash
ros2 launch vision_bot agv_nav_launch.py
```

**Active Nav2 nodes:**
- `controller_server` — MPPI controller
- `planner_server` — NavFn (A*)
- `behavior_server` — spin, backup, wait, assisted_teleop
- `bt_navigator` — navigate_to_pose, navigate_through_poses
- `velocity_smoother` — output smoothing
- `collision_monitor` — last-resort safety layer
- `waypoint_follower` — multi-goal mission execution
- `docking_server` — dock/undock support

**Send a navigation goal from CLI:**
```bash
ros2 action send_goal /navigate_to_pose nav2_msgs/action/NavigateToPose \
  "pose: {header: {frame_id: map}, pose: {position: {x: 2.0, y: 1.5, z: 0.0}, orientation: {w: 1.0}}}"
```

---

## Key Design Decisions

### 1. Aerial RGBD Camera — Overhead Obstacle Detection

A static RGBD depth camera is mounted at ceiling level in the Gazebo world. This is not part of the standard TurtleBot3 configuration.

**Why:** LiDAR on a ground robot detects obstacles at scan height (~0.2m). Objects on raised surfaces, low-hanging structures, or narrow vertical obstacles may be missed entirely. The overhead camera provides a top-down PointCloud2 that marks these into the local costmap voxel layer.

**TF design:** The camera requires a custom static transform to align its Gazebo frame with ROS 2 image conventions (Z-forward, X-right):

```python
# world_launch.py
arguments = [
    '0', '0', '0',              # no translation offset
    '-1.5708', '0', '-1.5708',  # RPY: rotate to REP-103 optical frame
    'aerial_rgbd_camera/link',
    'aerial_rgbd_camera_optical_frame'
]
```

**Costmap policy:** The aerial source is set `clearing: False` in the local costmap. A static overhead camera cannot reliably clear obstacles — it cannot distinguish "no obstacle" from "obstacle outside field of view". Only the LiDAR clears.

```yaml
# nav2_params.yaml
points:
  topic: /aerial_rgbd_camera/points
  clearing: False   # static overhead — must not clear LiDAR detections
  marking: True
  max_obstacle_height: 10.0
  z_voxels: 120     # 0.1m resolution × 120 = 12m vertical coverage
```

---

### 2. EKF Sensor Fusion — Velocity-Only Odometry

The EKF node from `robot_localization` fuses wheel odometry and IMU data. The critical design choice is fusing **velocities only** from the odometry source, not poses.

**Why:** Fusing absolute pose estimates from two independent integrating sources (wheel encoder odometry and IMU-integrated position) causes the EKF to attempt to reconcile conflicting pose estimates, amplifying drift rather than reducing it. The IMU provides heading correction; odometry provides forward velocity.

```yaml
# ekf.yaml
odom0_config: [false, false, false,   # x, y, z position — NOT fused
               false, false, false,   # roll, pitch, yaw — NOT fused
               true,  false, false,   # vx fused; vy=false (diff drive constraint)
               false, false, true,    # vyaw fused
               false, false, false]   # accelerations — not fused

imu0_config:  [false, false, false,
               false, false, true,    # yaw fused (heading correction)
               false, false, false,
               false, false, true,    # vyaw fused
               false, false, false]
```

**`vy = false` on odometry:** A differential-drive robot cannot move laterally. Fusing a near-zero y-velocity with high covariance from odometry introduces noise; setting it false is correct for this kinematic model.

---

## Configuration Reference

### `ekf.yaml` — EKF Localization

| Parameter | Value | Notes |
|-----------|-------|-------|
| `frequency` | 30 Hz | Filter output rate |
| `two_d_mode` | true | Ignores Z, roll, pitch — correct for planar AGV |
| `world_frame` | odom | Fuses for local odometry (not map-corrected) |
| `odom0` | `/odom` | Wheel encoder odometry source |
| `imu0` | `imu/data` | IMU source |

### `mapper_params_online_async.yaml` — SLAM Mapping

| Parameter | Value | Notes |
|-----------|-------|-------|
| `mode` | mapping | Online async SLAM |
| `resolution` | 0.05m | 5cm map cells |
| `max_laser_range` | 20.0m | LiDAR range for map rastering |
| `do_loop_closing` | true | Essential for large environments |
| `loop_match_minimum_chain_size` | 10 | Minimum scan chain for loop closure |

### `mapper_params_localization.yaml` — SLAM Localization

| Parameter | Value | Notes |
|-----------|-------|-------|
| `mode` | localization | Loads existing map |
| `map_file_name` | `...maps/my_world_map_serialize` | **Update this path for your system** |
| `map_start_at_dock` | true | Initial pose at origin |
| `scan_buffer_size` | 3 | Smaller than mapping (3 vs 10) — faster localization |

> ⚠️ **Important:** Update `map_file_name` in `mapper_params_localization.yaml` to the absolute path on your machine before running Phase 3.

### `nav2_params.yaml` — Navigation Stack

Key sections:

- **`controller_server`** — MPPI, 20Hz control loop, DiffDrive motion model
- **`local_costmap`** — 3×3m rolling window, dual-source voxel layer (LiDAR + RGBD)
- **`global_costmap`** — full map, static + obstacle + inflation layers
- **`planner_server`** — NavFn with A* (`use_astar: false` = Dijkstra by default; set `true` for A*)
- **`collision_monitor`** — footprint approach polygon, 1.2s time-to-collision threshold
- **`velocity_smoother`** — max 0.5 m/s, open-loop feedback

---

## License

This project is released for reference and evaluation purposes.  
ROS 2 and Nav2 are licensed under Apache 2.0.  
SLAM Toolbox is licensed under LGPL-2.1.

---

## Author

**Bineesh Ajabi**  
GitHub: [bineeshajabi](https://github.com/bineeshajabi)  
Repository: [Visual-enhanced-robot-nav](https://github.com/bineeshajabi/Visual-enhanced-robot-nav)
