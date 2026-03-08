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
colcon build --packages-select simple_ros_demo
source install/setup.bash
```

### 1. 运行 Publisher（速度发布者）

```bash
ros2 run simple_ros_demo sim_velocity_publisher.py


# 每 0.1 秒发布一次 Twist 消息到 /cmd_vel
# 日志示例
# [INFO] [velocity_publisher]: Published: linear.x = 1.0, angular.z = 0.5
```

### 2. 运行 Subscriber（速度监听与校验）
```bash
ros2 run simple_ros_demo velocity_subscriber.py
# 订阅 /cmd_vel，校验速度范围
# 日志示例（正常）
# [INFO] [velocity_subscriber]: OK: Received valid speed - linear=1.0, angular=0.5
```

### 3. 运行 Service Server（速度设置服务）
```bash
ros2 run simple_ros_demo speed_service_server.py
# 提供 /set_speed 服务
# 日志示例：
# [INFO] [speed_service_server]: SetSpeed service server started! Ready at /set_speed
```

### 4. 测试 Service 调用
在新终端：
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