#!/usr/bin/env bash
set -euo pipefail

workspace_dir="${1:-$HOME/ros2_demo_ws}"

if [[ ! -d "$workspace_dir" ]]; then
  echo "Workspace not found: $workspace_dir" >&2
  exit 1
fi

cd "$workspace_dir"

if [[ -f /opt/ros/humble/setup.bash ]]; then
  # Ensure ROS2 environment is available for build and tests.
  source /opt/ros/humble/setup.bash
fi

echo "==> Cleaning build artifacts"
rm -rf build/ install/ log/

echo "==> Building package"
colcon build --packages-select simple_ros_demo

echo "==> Sourcing workspace"
source install/setup.bash

echo "==> Running tests"
colcon test --packages-select simple_ros_demo

echo "==> Test results"
colcon test-result --verbose
