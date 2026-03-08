#!/usr/bin/env python3
# Copyright 2026 Reed
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist


class VelocityPublisher(Node):
    def __init__(self):
        super().__init__('velocity_publisher')  # 节点名字叫 velocity_publisher
        # 创建一个 Publisher：话题名 '/cmd_vel'，消息类型 Twist，队列大小 10
        self.publisher_ = self.create_publisher(Twist, '/cmd_vel', 10)

        # 创建一个定时器，每 0.1 秒（10Hz）调用一次 publish_velocity 函数
        timer_period = 0.1  # 秒
        self.timer = self.create_timer(timer_period, self.publish_velocity)

        # 初始速度值
        self.linear_speed = 1.0   # 前进 1 m/s
        self.angular_speed = 0.5  # 转弯 0.5 rad/s

        self.get_logger().info('Velocity Publisher started! Publishing at 10Hz')

    def publish_velocity(self):
        # 创建一个 Twist 消息
        msg = Twist()
        msg.linear.x = self.linear_speed   # 前进速度
        msg.angular.z = self.angular_speed  # 转弯速度（z 轴是 yaw，转向）

        # 发布消息
        self.publisher_.publish(msg)

        # 打印日志，看看是否在发
        self.get_logger().info(
            f'Published: linear.x = {msg.linear.x}, angular.z = {msg.angular.z}'
        )


def main(args=None):
    rclpy.init(args=args)  # 初始化 ROS2
    node = VelocityPublisher()  # 创建节点

    try:
        rclpy.spin(node)  # 让节点一直运行
    except KeyboardInterrupt:
        pass  # 捕获 Ctrl+C 或 SIGINT 信号
    finally:
        node.destroy_node()  # 清理节点资源
        if rclpy.ok():
            rclpy.shutdown()  # 关闭 ROS2


if __name__ == '__main__':
    main()

