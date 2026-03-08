# ROS2 Demo 项目测试指南

## 测试概述

本项目使用 **launch_testing + pytest** 框架对 ROS2 节点进行集成测试。当前实现了对 `sim_velocity_publisher.py` 发布者节点的频率校验测试。

## 测试依赖检查与安装

### 必需的测试依赖包

运行 `launch_testing` 测试需要以下 ROS2 包（大部分在 `ros-humble-desktop-full` 中已包含）：

- `ros-humble-launch-testing` - 核心测试框架
- `ros-humble-launch-testing-ament-cmake` - CMake 集成工具
- `ros-humble-launch-ros` - ROS2 节点启动支持
- `python3-pytest` - Python 测试框架

### 检查是否已安装

```bash
# 方法1: 检查 ROS2 包是否存在
dpkg -l | grep ros-humble-launch-testing

# 方法2: 尝试导入 Python 模块
python3 -c "import launch_testing; print('launch_testing 已安装')"
python3 -c "import pytest; print('pytest 已安装')"
```

### 安装缺失的依赖

如果检查发现缺少依赖，执行以下命令安装：

```bash
# 更新软件源
sudo apt update

# 安装测试相关依赖（一次性安装所有）
sudo apt install -y \
    ros-humble-launch-testing \
    ros-humble-launch-testing-ament-cmake \
    ros-humble-launch-ros \
    python3-pytest

# 可选：安装代码质量检查工具（如果要跑 linter 测试）
sudo apt install -y \
    ros-humble-ament-lint \
    ros-humble-ament-lint-auto \
    ros-humble-ament-lint-common
```

### 验证安装

安装完成后，验证依赖是否可用：

```bash
# 检查 pytest 版本
pytest --version

# 检查 ROS2 launch_testing 包
ros2 pkg list | grep launch_testing

# 预期输出：
# launch_testing
# launch_testing_ament_cmake
```

### 注意事项

1. **ROS2 Desktop vs Desktop-Full**:
   - `ros-humble-desktop-full` 通常已包含所有测试依赖
   - `ros-humble-desktop` 或最小化安装可能需要手动安装

2. **虚拟环境问题**:
   - 如果使用 Python 虚拟环境（venv/conda），确保能访问系统 ROS2 包
   - 建议直接使用系统 Python 3.10 运行测试

3. **权限问题**:
   - 安装 apt 包需要 `sudo` 权限
   - 确保当前用户在 sudoers 列表中

## 测试文件说明

### test_publisher_rate_launch.py

**位置**: `src/simple_ros_demo/test/test_publisher_rate_launch.py`

**功能**: 验证 Publisher 节点发布 `/cmd_vel` 话题的频率是否符合预期（10Hz ± 容差）

**测试原理**:
1. 使用 `launch_testing` 自动启动 `sim_velocity_publisher.py` 节点
2. 创建测试订阅者（`_RateProbe`）监听 `/cmd_vel` 并记录消息时间戳
3. 收集 **35 个样本**（丢弃前 5 个预热间隔以避免启动抖动）
4. 计算稳定阶段的平均消息间隔，推算实际发布频率
5. 断言实际频率是否在 **8Hz ~ 12Hz** 范围内（10Hz ± 2Hz）
6. 后置测试（`post_shutdown_test`）验证节点退出码是否正常

**关键参数**:
```python
TARGET_RATE_HZ = 10.0          # 目标频率
RATE_TOLERANCE_HZ = 2.0        # 容差范围
MIN_RATE_HZ = 8.0              # 最小可接受频率
MAX_RATE_HZ = 12.0             # 最大可接受频率
SAMPLES_TO_COLLECT = 35        # 收集样本数
WARMUP_INTERVALS_TO_DROP = 5   # 丢弃预热样本数
```

## 完整测试命令

> **前置条件**: 确保已完成上述"测试依赖检查与安装"步骤，所有依赖包已安装。

在 **ROS2 Humble 环境**（Ubuntu 22.04）执行以下命令：

```bash
# 1. 进入工作空间根目录
cd ~/ros2_demo_ws  # 或你的实际路径 /Users/Reed/dev/ros2_demo_ws

# 2. 清理旧构建（可选但推荐，避免缓存问题）
rm -rf build/ install/ log/

# 3. 构建项目
colcon build --packages-select simple_ros_demo

# 4. Source 环境（必须！否则测试无法找到节点）
source install/setup.bash

# 5. 运行测试（只跑当前包的测试）
colcon test --packages-select simple_ros_demo

# 6. 查看测试结果摘要
colcon test-result --verbose
```

## 预期输出

### 构建成功输出
```
Starting >>> simple_ros_demo
Finished <<< simple_ros_demo [2.5s]

Summary: 1 package finished [2.5s]
```

### 测试成功输出
运行 `colcon test-result --verbose` 后：

```
build/simple_ros_demo/test_results/simple_ros_demo/test_publisher_rate_launch.py.xunit.xml: 2 tests, 0 errors, 0 failures, 0 skipped
- test_publisher_rate_launch.py::test_cmd_vel_publish_rate_is_near_10hz
- test_publisher_rate_launch.py::test_exit_codes

Summary: 1 package finished [8.2s]
  1 package had stderr output: simple_ros_demo
```

> **注意**: "stderr output" 是正常的，ROS2 节点日志会输出到 stderr。

### 测试详细日志示例
```
test_publisher_rate_launch.py::test_cmd_vel_publish_rate_is_near_10hz PASSED
test_publisher_rate_launch.py::test_exit_codes PASSED

======================== 2 passed in 7.84s ========================
```

## 故障排查

### 问题0: 缺少测试依赖
**现象**:
```
ModuleNotFoundError: No module named 'launch_testing'
或
ModuleNotFoundError: No module named 'pytest'
```

**原因**: 测试框架依赖包未安装

**解决**:
```bash
# 安装所有测试依赖
sudo apt install -y \
    ros-humble-launch-testing \
    ros-humble-launch-testing-ament-cmake \
    ros-humble-launch-ros \
    python3-pytest

# 验证安装
pytest --version
ros2 pkg list | grep launch_testing
```

### 问题1: 测试找不到可执行文件
**现象**:
```
ExecutableNotFound: Executable 'sim_velocity_publisher.py' not found
```

**原因**: 没有 source 环境或构建未完成

**解决**:
```bash
source install/setup.bash
colcon build --packages-select simple_ros_demo
```

### 问题2: 频率测试失败
**现象**:
```
AssertionError: Publisher rate too low: measured=7.8Hz, expected >= 8.0Hz
```

**原因**: 
- 虚拟机性能不足导致节点调度延迟
- 系统负载过高
- 测试容差设置过严格

**解决**:
1. 临时方案：调整容差参数（修改 `test_publisher_rate_launch.py`）
   ```python
   RATE_TOLERANCE_HZ = 3.0  # 改为 ±3Hz（7Hz ~ 13Hz）
   ```

2. 根本方案：
   - 减少虚拟机其他进程负载
   - 增加虚拟机 CPU 核心数/内存分配
   - 在物理机上运行测试

### 问题3: 样本收集超时
**现象**:
```
AssertionError: Insufficient samples from /cmd_vel: got 18
```

**原因**: Publisher 节点未正常发布消息

**检查步骤**:
```bash
# 1. 手动启动 Publisher 检查是否正常
ros2 run simple_ros_demo sim_velocity_publisher.py

# 2. 另一个终端检查话题
ros2 topic list | grep cmd_vel
ros2 topic hz /cmd_vel
```

### 问题4: 查看完整测试日志
```bash
# 方法1: 查看 XML 测试报告
cat build/simple_ros_demo/test_results/simple_ros_demo/test_publisher_rate_launch.py.xunit.xml

# 方法2: 查看所有测试结果
colcon test-result --all --verbose

# 方法3: 查看节点运行日志
cat log/latest_test/simple_ros_demo/stdout_stderr.log
```

## 扩展测试用例（未来可添加）

### 1. Subscriber 节点测试
验证 `velocity_subscriber.py` 能否正确接收并校验消息：
- 测试正常速度范围内的消息是否输出 `OK` 日志
- 测试超范围速度是否输出 `WARNING` 日志

### 2. Service 服务端测试
验证 `speed_service_server.py` 的服务响应：
- 测试合法速度请求是否返回 `success=true`
- 测试非法速度请求是否返回 `success=false`
- 测试服务调用超时处理

### 3. 端到端集成测试
同时启动 Publisher + Subscriber：
- 验证消息端到端传递延迟
- 验证高负载下的消息丢失率

## 测试配置文件说明

### CMakeLists.txt 相关配置
```cmake
if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  ament_lint_auto_find_test_dependencies()

  # 注册 launch_testing 测试
  find_package(launch_testing_ament_cmake REQUIRED)
  add_launch_test(test/test_publisher_rate_launch.py TIMEOUT 40)
endif()
```

- `TIMEOUT 40`: 测试超时时间 40 秒（包括启动节点+收集样本+关闭节点）

### package.xml 测试依赖
```xml
<test_depend>ament_lint_auto</test_depend>
<test_depend>ament_lint_common</test_depend>
<test_depend>launch_testing</test_depend>
<test_depend>launch_testing_ament_cmake</test_depend>
<test_depend>launch_ros</test_depend>
```

- `launch_testing`: 核心 launch 测试框架
- `launch_testing_ament_cmake`: CMake 集成工具
- `launch_ros`: ROS2 节点启动支持

## 最佳实践建议

1. **每次修改代码后必测**: 确保回归
2. **清理构建缓存**: 避免旧代码干扰 `rm -rf build/ install/ log/`
3. **CI/CD 集成**: 将 `colcon test` 加入 GitHub Actions/Jenkins 流水线
4. **测试隔离**: 每个测试用独立的 launch 启动节点，避免状态污染
5. **容差设置**: 根据硬件性能调整，不要过于严格或宽松
6. **日志记录**: 保存失败时的完整日志用于复现分析

## 常见问题 FAQ

**Q: 运行测试需要额外安装依赖吗？**  
A: 如果使用 `ros-humble-desktop-full` 安装，测试依赖通常已包含。否则需要安装：
```bash
sudo apt install -y ros-humble-launch-testing \
    ros-humble-launch-testing-ament-cmake \
    ros-humble-launch-ros python3-pytest
```
详见"测试依赖检查与安装"章节。

**Q: 为什么要丢弃前 5 个预热样本？**  
A: 节点启动阶段存在初始化开销（创建 Publisher、加载库等），前几次发布间隔可能不稳定，丢弃后计算更准确。

**Q: 为什么用 `time.monotonic()` 而不是 ROS 时间？**  
A: `monotonic()` 不受系统时钟调整影响，更适合测量时间间隔。ROS 时间在仿真场景下可能被加速/减速。

**Q: 测试能在没有 ROS2 环境的机器上跑吗？**  
A: 不能。`launch_testing` 依赖完整的 ROS2 运行时（rclpy、DDS中间件等），必须在安装了 ROS2 的环境运行。

**Q: 如何并行跑多个包的测试？**  
A: `colcon test --parallel-workers 4`（4 个并发工作线程）

---

**文档维护**: 2026年3月8日  
**适用版本**: ROS2 Humble Hawksbill  
**测试框架**: launch_testing 1.0.x + pytest 7.x
