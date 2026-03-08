# ROS2 四个终端命令理解整理

## 文档目的
将四个终端命令的作用、你的理解和标准解释整理为统一格式，便于复习 ROS2 中 `Topic` 与 `Service` 的区别。

## 总览
1. 终端1：启动发布者，持续向 `/cmd_vel` 发布速度指令（10Hz）。
2. 终端2：启动订阅者，被动接收 `/cmd_vel` 并做速度安全校验。
3. 终端3：启动服务端，提供 `/set_speed` 服务。
4. 终端4：作为客户端调用 `/set_speed`，一次性请求修改速度。

## 终端1：Publisher

```bash
ros2 run simple_ros_demo sim_velocity_publisher.py
```

**你的理解**
每隔 0.1 秒发一个状态消息到频道里，即 10Hz（每秒 10 次）。

**结论**
完全正确。

**标准说明**
- 这是发布者节点（Publisher）。
- 它每 0.1 秒向 `/cmd_vel` 发布一次 `geometry_msgs/Twist` 消息。
- 典型消息内容：`linear.x = 1.0`，`angular.z = 0.5`。
- 10Hz 表示持续广播的实时指令流，适合机器人运动控制场景。

## 终端2：Subscriber

```bash
ros2 run simple_ros_demo velocity_subscriber.py
```

**你的理解**
订阅频道接收消息，持续校验并输出日志；若发布频率为 10Hz，则每秒也会处理 10 次。

**结论**
基本正确，关键点是“被动接收”。

**标准说明**
- 这是订阅者节点（Subscriber），订阅 `/cmd_vel`。
- 每收到一条消息就立刻回调处理：提取线性/角速度并校验阈值。
- 校验规则：线性速度 `<= 2.0`，角速度 `<= 1.0`。
- 它不是主动“发送 10 次”，而是跟随发布者节奏被动处理（发布者 10Hz，则它通常处理 10Hz）。
- 可理解为安全监护模块：对速度指令做实时审查并输出 `OK/WARNING` 日志。

## 终端3：Service Server

```bash
ros2 run simple_ros_demo speed_service_server.py
```

**你的理解**
在某个频道里监听，并提供修改速度的服务。

**结论**
部分正确，需要区分 `Service` 与 `Topic`。

**标准说明**
- 这是服务端节点（Service Server），提供 `/set_speed` 服务。
- 它不是订阅话题，不是“监听频道”。
- 服务模型是请求-响应（request-response）：收到请求后校验并返回 `success/message`。
- 它不会持续发布消息，只在被客户端调用时响应。
- 这类机制适合“一次性配置”操作，如临时修改参数。

## 终端4：Service Client 调用

```bash
ros2 service call /set_speed simple_ros_demo/srv/SetSpeed "{target_linear: 1.2, target_angular: 0.4}"
```

**你的理解**
偶尔执行一次用于修改速度，猜测是把命令发到终端3对应的频道。

**结论**
总体正确，但“频道”这一点需要纠正。

**标准说明**
- 这是服务客户端调用，不是话题发布。
- 客户端把请求发到 `/set_speed` 服务端点，服务端处理后同步返回结果。
- 调用是一次性的，不是持续流。
- 可理解为“点对点对话”，而非“群广播”。

## Topic 与 Service 一句话对比

- `Topic`：发布-订阅，异步，持续广播，适合实时数据流。
- `Service`：请求-响应，同步，一次一答，适合配置/触发类操作。

## 本场景通信关系

1. `sim_velocity_publisher.py` 持续发布 `/cmd_vel`。
2. `velocity_subscriber.py` 持续接收并校验 `/cmd_vel`。
3. `speed_service_server.py` 挂载 `/set_speed` 服务，等待调用。
4. `ros2 service call ...` 作为客户端向 `/set_speed` 发起一次请求并等待响应。