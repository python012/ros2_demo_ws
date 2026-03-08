# ROS2 简单 Demo 项目使用与调试指南

## 项目介绍
这是一个使用 Python (rclpy) 编写的 ROS2 Humble 入门级 Demo 项目，包含三个核心节点：

- **Publisher**：以 10Hz 频率发布 `geometry_msgs/Twist` 消息（模拟速度指令），话题名为 `/cmd_vel`。
- **Subscriber**：订阅 `/cmd_vel` 话题，接收 Twist 消息并进行简单速度校验（线性速度 ≤ 2.0 m/s，角速度 ≤ 1.0 rad/s），输出 OK 或警告日志。
- **Service Server**：提供自定义服务 `/set_speed`（类型 `simple_ros_demo/srv/SetSpeed`），允许外部设置目标速度，返回是否成功及说明消息。

项目目标：演示 ROS2 的发布-订阅机制 + 服务调用机制，帮助初学者理解节点间通信、自定义接口（.srv）的创建与使用。

项目地址：https://github.com/python012/ros2_demo_ws

## 背景介绍
ROS2（Robot Operating System 2）是机器人软件开发的框架，其核心通信机制包括：

- **Topic（发布-订阅）**：一对多、异步、持续广播，适合传感器数据、速度指令等实时流。
- **Service（请求-响应）**：一对一、同步、有明确回复，适合配置参数、触发动作等一次性操作。

本项目通过一个简单的“速度控制”场景，完整实现了以上两种机制：
- Publisher → Subscriber：实时指令传递与安全校验。
- Service：外部动态修改速度（可扩展到真实机器人控制）。

## 使用环境
- **操作系统**：Ubuntu 22.04 LTS（arm64 架构，推荐在 UTM 虚拟机或物理 ARM 设备上运行）
- **ROS2 发行版**：Humble Hawksbill（ros-humble-desktop-full）
- **Python 版本**：3.10（Ubuntu 22.04 默认）
- **虚拟机工具**（可选）：UTM（Mac M1/M2 上运行 Ubuntu arm64）
- **推荐硬件**：MacBook Pro M1/M2 + UTM（8GB+ 内存分配给 VM）

## 依赖安装
在 Ubuntu 终端执行：

```bash
# 更新系统 & 安装 ROS2 依赖
sudo apt update
sudo apt install ros-humble-desktop-full python3-colcon-common-extensions -y

# 安装接口生成工具（自定义 srv 必须）
sudo apt install ros-humble-rosidl-default-generators ros-humble-rosidl-default-runtime ros-humble-rosidl-generator-py -y

# 全局 source ROS2（建议加到 ~/.bashrc）
echo "source /opt/ros/humble/setup.bash" >> ~/.bashrc
source ~/.bashrc
```

## 构建项目

```bash
rm -rf build/ install/ log/
colcon build --packages-select simple_ros_demo
source install/setup.bash
```

### 1. 运行 Publisher（速度发布者）
终端1
```bash
ros2 run simple_ros_demo sim_velocity_publisher.py
# 每 0.1 秒发布一次 Twist 消息到 /cmd_vel
# 日志示例
# [INFO] [velocity_publisher]: Published: linear.x = 1.0, angular.z = 0.5
```

### 2. 运行 Subscriber（速度监听与校验）
终端2
```bash
ros2 run simple_ros_demo velocity_subscriber.py
# 订阅 /cmd_vel，校验速度范围
# 日志示例（正常）
# [INFO] [velocity_subscriber]: OK: Received valid speed - linear=1.0, angular=0.5
```

### 3. 运行 Service Server（速度设置服务）
终端3
```bash
ros2 run simple_ros_demo speed_service_server.py
# 提供 /set_speed 服务
# 日志示例：
# [INFO] [speed_service_server]: SetSpeed service server started! Ready at /set_speed
```

### 4. 测试 Service 调用
终端4
```bash
# 正常速度
ros2 service call /set_speed simple_ros_demo/srv/SetSpeed "{target_linear: 1.2, target_angular: 0.4}"

# 超范围速度（会返回失败）
ros2 service call /set_speed simple_ros_demo/srv/SetSpeed "{target_linear: 3.0, target_angular: 0.0}"
```
预期响应：
```text
response:
  success: true
  message: 'Success: speed set!'
```

### 调试技巧

- 查看节点日志：`ros2 run ... --ros-args --log-level debug`
- 查看话题：`ros2 topic list`、`ros2 topic echo /cmd_vel`
- 查看服务：`ros2 service list`、`ros2 service type /set_speed`
- 查看接口：`ros2 interface show simple_ros_demo/srv/SetSpeed`

# SetSpeed 服务节点调试问题总结（昨天到今天）

## 问题概述
从昨天开始到今天，`speed_service_server.py` 节点一直无法正常运行。主要表现为：
- 构建成功，但 `ros2 run` 报错
- 早期：ModuleNotFoundError（找不到 `simple_ros_demo.srv.SetSpeed`）
- 中期：构建日志无 srv 生成记录
- 后期：Exec format error 或 no executable found

最终解决：加了 shebang 头 + 确认可执行权限 + 正确 source 环境

## 问题演变过程及原因

- **阶段1：ModuleNotFoundError: No module named 'simple_ros_demo.srv'**
   - 表现：运行时报 `cannot import name 'SetSpeed' from 'simple_ros_demo.srv'`
   - 原因：自定义 srv 接口没有生成 Python 模块（_SetSpeed.py 等文件缺失）
   - 根因：
     - package.xml 缺少或位置错误的 `<rosidl_generate_interfaces>`
     - setup.py 的 data_files glob 路径写错（没捕获 srv 文件）
     - ament_python 类型默认不触发 rosidl 生成
   - 解决过程：切换到 ament_cmake + 修正 CMakeLists.txt 中的路径 + 添加 rosidl_generate_interfaces

- 阶段2：构建成功但 srv 目录仍未生成**
   - 表现：ls install/.../site-packages/simple_ros_demo/srv/ 为空
   - 原因：CMakeLists.txt 中的 srv 文件路径写错（应为 "simple_ros_demo/srv/SetSpeed.srv"）
   - 解决：修正 rosidl_generate_interfaces 的相对路径参数

- **阶段3：构建成功、srv 生成，但运行 no executable found**
   - 表现：ros2 run 找不到可执行文件
   - 原因：install(PROGRAMS) 安装了 .py 文件，但 ros2 pkg executables 显示带 .py 后缀
   - 解决：运行时带 .py 后缀：`ros2 run simple_ros_demo speed_service_server.py`

- **阶段4：最终报错 Exec format error**
   - 表现：OSError: [Errno 8] Exec format error
   - 原因：Python 脚本缺少 shebang 行（#!/usr/bin/env python3），系统无法识别如何执行
   - 解决：在 speed_service_server.py 第一行添加：
     ```python
     #!/usr/bin/env python3
     ```
   - 额外检查：确保文件具有可执行权限（chmod +x speed_service_server.py），然后重新 colcon build

## 最终成功条件（当前状态）
- srv 接口已生成（_SetSpeed.py 等存在）
- 脚本有 shebang 头 + 可执行权限（-rwxr-xr-x）
- ros2 pkg executables 能列出带 .py 的节点
- 正确 source install/setup.bash
- 运行命令：`ros2 run simple_ros_demo speed_service_server.py`
- 服务调用成功返回 success: true

## 经验教训
- ROS2 自定义接口（srv/msg）生成是最容易卡的点，必须同时满足：
- package.xml 有 rosidl 生成依赖 + <rosidl_generate_interfaces>
- CMakeLists.txt 正确路径 + rosidl_generate_interfaces 调用
- 清理 build/install/log 后全量构建
- Python 脚本作为节点必须有 shebang（`#!/usr/bin/env python3`），否则 Exec format error
- ros2 run 时可能需要带 .py 后缀（视 install(PROGRAMS) 输出而定）
- 每次修改后都要清理 + `colcon build` + `source install/setup.bash`
- 日志是关键：构建时看是否有 “Generating Python from SRV”

## 建议后续优化
- 在所有 .py 节点首行统一加 shebang
- 尝试让 Publisher 从 Service 更新速度，实现完整闭环
- 未来项目优先用 ament_cmake + 接口包分离（更稳定）
