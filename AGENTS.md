# AGENTS.md - ROS2 Demo 项目总结

## 项目概述

这是一个 ROS2 Humble 入门级 Demo 项目，使用 Python (rclpy) 实现，展示了 ROS2 的核心通信机制：**发布-订阅模式**和**服务调用模式**。项目通过"速度控制"场景，帮助开发者理解机器人软件中的节点通信原理。

### 项目元信息
- **项目名称**: simple_ros_demo
- **ROS2 发行版**: Humble Hawksbill
- **编程语言**: Python 3.10
- **构建系统**: ament_cmake + setuptools
- **许可证**: Apache-2.0

---

## 项目结构

```
ros2_demo_ws/
├── src/
│   └── simple_ros_demo/              # 主功能包
│       ├── simple_ros_demo/          # Python 模块目录
│       │   ├── __init__.py
│       │   ├── sim_velocity_publisher.py   # 发布者节点
│       │   ├── velocity_subscriber.py      # 订阅者节点
│       │   ├── speed_service_server.py     # 服务端节点
│       │   └── srv/
│       │       └── SetSpeed.srv           # 自定义服务接口
│       ├── test/                     # 测试文件
│       │   ├── test_flake8.py
│       │   ├── test_pep257.py
│       │   └── test_copyright.py
│       ├── resource/                 # ROS2 资源标记
│       ├── CMakeLists.txt            # CMake 构建配置
│       ├── package.xml               # ROS2 包清单
│       └── setup.py                  # Python 包配置
├── DEBUG.md                          # 使用与调试指南
├── .gitignore
└── AGENTS.md                         # 本文件
```

---

## 核心组件详解

### 1. VelocityPublisher (发布者节点)
**文件**: `sim_velocity_publisher.py`

**功能**: 以 10Hz 频率发布速度指令到 `/cmd_vel` 话题

**关键实现**:
- 继承 `rclpy.node.Node` 类创建节点
- 使用 `create_publisher()` 创建发布者，消息类型为 `geometry_msgs/Twist`
- 使用 `create_timer()` 创建定时器，实现周期性发布
- 发布内容: 线性速度 1.0 m/s，角速度 0.5 rad/s

**核心代码模式**:
```python
self.publisher_ = self.create_publisher(Twist, '/cmd_vel', 10)
self.timer = self.create_timer(0.1, self.publish_velocity)
```

### 2. VelocitySubscriber (订阅者节点)
**文件**: `velocity_subscriber.py`

**功能**: 订阅 `/cmd_vel` 话题，接收速度消息并进行安全校验

**关键实现**:
- 使用 `create_subscription()` 创建订阅者
- 回调函数 `listener_callback()` 处理接收到的消息
- **速度校验规则**:
  - 线性速度阈值: |linear| ≤ 2.0 m/s
  - 角速度阈值: |angular| ≤ 1.0 rad/s
- 超范围时输出警告日志，正常时输出确认日志

**核心代码模式**:
```python
self.subscription = self.create_subscription(
    Twist, '/cmd_vel', self.listener_callback, 10)
```

### 3. SpeedServiceServer (服务端节点)
**文件**: `speed_service_server.py`

**功能**: 提供自定义服务 `/set_speed`，允许外部设置目标速度

**关键实现**:
- 使用 `create_service()` 创建服务端
- 服务类型: `simple_ros_demo/srv/SetSpeed` (自定义接口)
- 服务回调函数 `handle_set_speed()` 处理请求
- 返回设置结果 (成功/失败 + 说明消息)

**核心代码模式**:
```python
self.srv = self.create_service(SetSpeed, 'set_speed', self.handle_set_speed)
```

### 4. SetSpeed.srv (自定义服务接口)
**文件**: `simple_ros_demo/srv/SetSpeed.srv`

**接口定义**:
```
# 请求部分
float64 target_linear   # 目标线性速度
float64 target_angular  # 目标角速度
---
# 响应部分
bool success            # 是否设置成功
string message          # 说明文字
```

**生成方式**: 通过 `rosidl_generate_interfaces()` 在构建时自动生成 Python/Cpp 接口代码

---

## 构建系统

### ament_cmake + setuptools 混合构建

此项目采用**混合构建方式**：
- **CMakeLists.txt**: 负责 ROS2 接口生成和资源安装
- **setup.py**: 负责 Python 包管理和入口点配置

**为什么混合使用？**
- ROS2 自定义接口 (.srv/.msg/.action) 需要 CMake 的 `rosidl_generate_interfaces()` 生成
- Python 节点需要 setuptools 的 `entry_points` 注册为可执行命令

### 构建流程

```bash
# 1. 编译
colcon build --packages-select simple_ros_demo

# 2. source 环境
source install/setup.bash

# 3. 运行节点
ros2 run simple_ros_demo velocity_publisher
ros2 run simple_ros_demo velocity_subscriber
ros2 run simple_ros_demo speed_service_server
```

---

## ROS2 通信机制总结

### Topic (发布-订阅)
- **模式**: 一对多，异步，持续广播
- **适用场景**: 传感器数据流、速度指令流等实时数据
- **本项目示例**: `/cmd_vel` 话题传输速度指令

### Service (请求-响应)
- **模式**: 一对一，同步，有明确回复
- **适用场景**: 配置参数、触发动作等一次性操作
- **本项目示例**: `/set_speed` 服务设置目标速度

---

## 关键技术点

### 1. 节点生命周期
```python
rclpy.init()        # 初始化 ROS2 客户端库
node = MyNode()     # 创建节点实例
rclpy.spin(node)    # 进入事件循环，处理回调
rclpy.shutdown()    # 清理资源
```

### 2. 消息类型
- `geometry_msgs/Twist`: 包含线性和角速度的 3D 运动指令
  - `linear.x/y/z`: 线性速度 (m/s)
  - `angular.x/y/z`: 角速度 (rad/s)

### 3. 队列大小 (Queue Size)
- 发布/订阅时设置的队列大小 (本项目均为 10)
- 作用: 缓冲消息，处理速度不匹配的情况
- 队列满时: 旧消息被丢弃 (FIFO)

### 4. 回调函数
- 订阅者回调: `listener_callback(msg)` 接收话题消息
- 服务端回调: `handle_set_speed(request, response)` 处理服务请求

---

## 开发约定

### 代码风格
- 遵循 Python PEP 8 规范 (通过 test_flake8.py 检查)
- 遵循 PEP 257 文档字符串规范 (通过 test_pep257.py 检查)
- 版权声明检查 (test_copyright.py)

### 日志级别
- `INFO`: 正常操作日志
- `WARN`: 异常情况但可继续运行
- `DEBUG`: 调试信息 (需手动启用)

### 安全校验
速度限制在多处实现:
- 订阅者: 校验并报警
- 服务端: 校验并拒绝设置

---

## 测试与调试

### 测试命令
```bash
# 运行 linter 测试
pytest test/

# 查看话题
ros2 topic list
ros2 topic echo /cmd_vel
ros2 topic info /cmd_vel

# 查看服务
ros2 service list
ros2 service type /set_speed
ros2 service call /set_speed simple_ros_demo/srv/SetSpeed "{target_linear: 1.0, target_angular: 0.5}"

# 查看接口
ros2 interface show simple_ros_demo/srv/SetSpeed
```

### 调试技巧
```bash
# 启用 DEBUG 日志
ros2 run simple_ros_demo velocity_publisher --ros-args --log-level debug

# 查看节点信息
ros2 node list
ros2 node info /velocity_publisher
```

---

## 扩展方向

### 可添加功能
1. **参数服务器**: 使用 ROS2 参数动态配置速度值
2. **Launch 文件**: 编写 Python/XML launch 文件同时启动多个节点
3. **Action**: 实现耗时操作的异步反馈 (如导航任务)
4. **TF 坐标变换**: 添加坐标系转换
5. **数据记录**: 使用 ros2 bag 记录话题数据

### 真实机器人集成
- 替换 `/cmd_vel` 发布者为真实传感器数据
- 替换订阅者为真实电机控制器接口
- 添加安全监控节点 (急停、避障等)

---

## 常见问题

### Q: 为什么使用 Twist 消息？
A: `geometry_msgs/Twist` 是 ROS 中表示速度的标准消息类型，被大多数机器人控制接口 (如 TurtleBot、Gazebo) 支持。

### Q: 为什么速度限制是 linear ≤ 2.0, angular ≤ 1.0？
A: 这是演示用的安全阈值，实际项目中应根据机器人硬件规格设定。

### Q: 如何添加新的消息/服务接口？
A: 在 `simple_ros_demo/msg/` 或 `simple_ros_demo/srv/` 创建 `.msg`/`.srv` 文件，然后在 CMakeLists.txt 的 `rosidl_generate_interfaces()` 中添加引用。

---

## 依赖清单

| 依赖项 | 用途 |
|--------|------|
| `rclpy` | ROS2 Python 客户端库 |
| `geometry_msgs` | 几何消息类型 (Twist) |
| `std_srvs` | 标准服务类型 |
| `rosidl_default_generators` | 接口代码生成器 |
| `ament_cmake` | ROS2 构建工具 |

---

## 总结

本项目是一个**教科书级别的 ROS2 入门项目**，完整展示了:
1. 节点的创建与生命周期管理
2. 发布-订阅通信模式
3. 服务调用通信模式
4. 自定义接口 (.srv) 的定义与使用
5. 混合构建系统的配置 (ament_cmake + setuptools)
6. 基本的安全校验与日志记录

适合作为学习 ROS2 的第一个实战项目，代码结构清晰，注释详细，可作为后续复杂机器人项目的模板基础。