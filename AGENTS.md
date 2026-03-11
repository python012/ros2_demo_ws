# AGENTS.md - Agent Guidelines for ROS2 Demo Project

## Project Overview
- **Project**: simple_ros_demo
- **ROS2 Distro**: Humble Hawksbill
- **Language**: Python 3.10
- **Build System**: ament_cmake + setuptools (hybrid)

---

## Build & Test Commands

### Build
```bash
colcon build --packages-select simple_ros_demo
source install/setup.bash
```

### Run All Tests
```bash
# Full test suite with build
./scripts/run_tests.sh

# Or manually:
rm -rf build/ install/ log/
colcon build --packages-select simple_ros_demo
source install/setup.bash
colcon test --packages-select simple_ros_demo
colcon test-result --verbose

# Linter tests only (runs flake8, pep257, copyright)
pytest src/simple_ros_demo/test/
```

### Run Single Test
```bash
# Run specific linter test
pytest src/simple_ros_demo/test/test_flake8.py
pytest src/simple_ros_demo/test/test_pep257.py
pytest src/simple_ros_demo/test/test_copyright.py

# Run with specific marker
pytest src/simple_ros_demo/test/ -m flake8
pytest src/simple_ros_demo/test/ -m pep257
pytest src/simple_ros_demo/test/ -m copyright
```

### Run Nodes
```bash
ros2 run simple_ros_demo velocity_publisher
ros2 run simple_ros_demo velocity_subscriber
ros2 run simple_ros_demo speed_service_server
```

---

## Code Style Guidelines

### General Rules
- Follow PEP 8 (checked by test_flake8.py)
- Follow PEP 257 docstring conventions (checked by test_pep257.py)
- Apache 2.0 license header required (checked by test_copyright.py)

### Imports
```python
# Standard - order matters (std lib, third-party, local)
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from simple_ros_demo.srv import SetSpeed
```

### Naming Conventions
- **Classes**: `PascalCase` (e.g., `VelocityPublisher`, `SpeedServiceServer`)
- **Functions/methods**: `snake_case` (e.g., `publish_velocity`, `listener_callback`)
- **Variables**: `snake_case` (e.g., `linear_speed`, `target_linear`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `MAX_LINEAR_SPEED = 2.0`)
- **Private members**: Prefix with `_` (e.g., `self._internal_state`)

### Node Implementation Pattern
```python
#!/usr/bin/env python3
# Copyright 2026 [Author Name]
#
# Licensed under the Apache License, Version 2.0 (the "License");
# ...

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist


class MyNode(Node):
    def __init__(self):
        super().__init__('node_name')
        # Create publishers/subscribers/services here
        self.get_logger().info('Node started!')

    def my_callback(self, msg):
        # Handle message
        self.get_logger().info(f'Received: {msg.data}')


def main(args=None):
    rclpy.init(args=args)
    node = MyNode()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
```

### Error Handling
- Use try/except for `rclpy.spin()` to handle `KeyboardInterrupt`
- Always call `node.destroy_node()` and `rclpy.shutdown()` in `finally` block
- Use `rclpy.ok()` check before shutdown to avoid errors on nested contexts

### Logging
- Use node's built-in logger: `self.get_logger().info/warn/error()`
- Log levels: INFO (normal), WARN (recoverable), ERROR (failure)
- Use f-strings for log messages: `f'Value: {value}'`

### ROS2 Specific
- Queue size: typically 10 for publishers/subscribers
- Topic names: use absolute paths with `/` prefix (e.g., `/cmd_vel`)
- Service names: use relative paths (e.g., `set_speed`)
- Always handle shutdown gracefully with `KeyboardInterrupt`

---

## File Structure
```
src/simple_ros_demo/
├── simple_ros_demo/
│   ├── __init__.py
│   ├── sim_velocity_publisher.py
│   ├── velocity_subscriber.py
│   ├── speed_service_server.py
│   └── srv/
│       └── SetSpeed.srv
├── test/
│   ├── test_flake8.py
│   ├── test_pep257.py
│   └── test_copyright.py
├── CMakeLists.txt
├── package.xml
└── setup.py
```

---

## Key Patterns

### Publisher
```python
self.publisher_ = self.create_publisher(Twist, '/topic', 10)
self.timer = self.create_timer(period, self.callback)
```

### Subscriber
```python
self.subscription = self.create_subscription(
    Twist, '/topic', self.callback, 10)
```

### Service Server
```python
self.srv = self.create_service(MyService, 'service_name', self.callback)
```

### Service Client
```python
self.client = self.create_client(MyService, 'service_name')
```