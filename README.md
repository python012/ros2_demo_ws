# simple_ros_demo

一个简洁的 ROS2 Humble 入门级 Demo 项目，使用 Python (rclpy) 实现，展示了 ROS2 的核心通信机制：**发布-订阅模式**和**服务调用模式**。

## 运行环境

- **操作系统**: Ubuntu 22.04 (Jammy Jellyfish)
- **ROS2 发行版**: Humble Hawksbill
- **编程语言**: Python 3.10
- **构建系统**: ament_cmake + setuptools (混合)
- **许可证**: Apache-2.0

> **注意**: 本项目依赖 ROS2 Humble，需先安装 ROS2 环境。推荐安装 `ros-humble-desktop-full` 以获取完整依赖。

### 核心功能

本项目通过"速度控制"场景演示 ROS2 通信：
1. **VelocityPublisher**: 以 10Hz 频率发布速度指令到 `/cmd_vel` 话题
2. **VelocitySubscriber**: 订阅 `/cmd_vel` 话题，接收并进行速度校验
3. **SpeedServiceServer**: 提供 `/set_speed` 服务，允许动态设置目标速度

---

## 快速开始

### 构建

```bash
cd /home/reed/ros2_demo_ws
colcon build --packages-select simple_ros_demo
source install/setup.bash
```

### 运行节点

```bash
# 终端1：启动发布者
ros2 run simple_ros_demo velocity_publisher

# 终端2：启动订阅者
ros2 run simple_ros_demo velocity_subscriber

# 终端3：启动服务节点
ros2 run simple_ros_demo speed_service_server

# 终端4：调用服务
ros2 service call /set_speed simple_ros_demo/srv/SetSpeed "{target_linear: 1.0, target_angular: 0.5}"
```

---

## 测试

### 运行全部测试

```bash
./scripts/run_tests.sh
```

或手动执行：

```bash
rm -rf build/ install/ log/
colcon build --packages-select simple_ros_demo
source install/setup.bash
colcon test --packages-select simple_ros_demo
colcon test-result --verbose
```

### 运行特定测试

```bash
# 仅运行 linter 测试
pytest src/simple_ros_demo/test/

# 运行单个 linter 测试
pytest src/simple_ros_demo/test/test_flake8.py
pytest src/simple_ros_demo/test/test_pep257.py
pytest src/simple_ros_demo/test/test_copyright.py

# 按标记运行
pytest src/simple_ros_demo/test/ -m flake8
pytest src/simple_ros_demo/test/ -m pep257
pytest src/simple_ros_demo/test/ -m copyright
```

### 测试类型

| 测试文件 | 说明 |
|---------|------|
| `test_flake8.py` | PEP8 代码风格检查 |
| `test_pep257.py` | Docstring 格式检查 |
| `test_copyright.py` | Apache 2.0 许可证头检查 |
| `test_publisher_rate_launch.py` | 发布者节点启动和发布频率测试 |
| `test_subscriber_lifecycle_launch.py` | 订阅者节点生命周期测试 |
| `test_speed_service_launch.py` | 服务节点功能测试 |

---

## 项目结构

```
ros2_demo_ws/
├── src/simple_ros_demo/
│   ├── simple_ros_demo/
│   │   ├── __init__.py
│   │   ├── sim_velocity_publisher.py   # 发布者节点
│   │   ├── velocity_subscriber.py     # 订阅者节点
│   │   ├── speed_service_server.py    # 服务端节点
│   │   └── srv/
│   │       └── SetSpeed.srv           # 自定义服务接口
│   ├── test/                          # 测试文件
│   ├── CMakeLists.txt                # CMake 构建配置
│   ├── package.xml                   # ROS2 包清单
│   └── setup.py                       # Python 包配置
├── scripts/
│   └── run_tests.sh                   # 测试脚本
└── AGENTS.md                          # Agent 指南
```

---

## 调试技巧

```bash
# 查看话题
ros2 topic list
ros2 topic echo /cmd_vel

# 查看服务
ros2 service list
ros2 service call /set_speed simple_ros_demo/srv/SetSpeed "{target_linear: 1.0, target_angular: 0.5}"

# 查看节点
ros2 node list
ros2 node info /velocity_publisher
```

---

## 经验总结：Python 模块搜索路径冲突问题

### 问题描述

在运行集成测试时遇到 `ImportError: cannot import name 'SetSpeed' from 'simple_ros_demo.srv'`

### 根因分析

1. **pytest 从源码目录运行**: `pytest` 从 `src/simple_ros_demo/test/` 目录执行
2. **sys.path 优先级**: Python 的 `sys.path` 首先包含空字符串 `''`（当前目录），即源码目录
3. **包查找顺序**: Python 找到源码中的 `simple_ros_demo` 包，但该包只有手动编写的 Python 文件
4. **缺失生成代码**: 源码目录中的 `simple_ros_demo` 没有 `srv` 子目录（生成的 Python 接口代码位于 `install/` 目录）

### 解决方案

#### 1. CMakeLists.txt 中安装生成的 Python 接口

```cmake
# 安装生成的 Python 接口到 lib 目录
install(DIRECTORY
  ${CMAKE_BINARY_DIR}/rosidl_generator_py/${PROJECT_NAME}/srv
  DESTINATION lib/${PROJECT_NAME}
)
```

#### 2. 测试文件中修复 sys.path

在 `test_speed_service_launch.py` 开头添加路径修复逻辑，确保优先使用安装目录的包：

```python
import os
import sys

# 移除可能遮盖安装包的源码路径
_this_dir = os.path.dirname(os.path.abspath(__file__))
_pkg_dir = os.path.dirname(os.path.dirname(_this_dir))
_workspace_dir = os.path.dirname(_pkg_dir)

_filtered_path = []
for p in sys.path:
    if p in ('', _pkg_dir, _workspace_dir):
        continue
    _filtered_path.append(p)

# 预置安装包位置
_install_base = None
for p in _filtered_path:
    if '/local/lib/python' in p and 'dist-packages' in p:
        _install_base = p
        break

if _install_base:
    _installed_pkg = os.path.join(_install_base, 'simple_ros_demo')
    if os.path.isdir(_installed_pkg):
        _filtered_path.insert(0, _installed_pkg)

sys.path = _filtered_path
```

### 教训

- ROS2 混合构建项目（ament_cmake + setuptools）中，生成的 Python 接口需要显式安装
- 测试代码从源码目录运行时，需要注意模块搜索路径优先级
- 调试 import 问题时，可通过打印 `sys.path` 和 `simple_ros_demo.__path__` 定位问题
