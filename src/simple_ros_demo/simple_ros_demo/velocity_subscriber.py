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


class VelocitySubscriber(Node):
    def __init__(self):
        super().__init__('velocity_subscriber')  # 节点名字
        # 创建订阅：话题 '/cmd_vel'，消息类型 Twist，回调函数 listener_callback，队列大小 10
        self.subscription = self.create_subscription(
            Twist,
            '/cmd_vel',
            self.listener_callback,
            10)
        self.get_logger().info('Velocity Subscriber started! Listening to /cmd_vel')

    def listener_callback(self, msg):
        # 收到消息后，提取速度
        linear = msg.linear.x
        angular = msg.angular.z

        # 简单校验
        if abs(linear) > 2.0 or abs(angular) > 1.0:
            self.get_logger().warn(
                f'WARNING: Invalid speed! linear={linear}, angular={angular}'
            )
        else:
            self.get_logger().info(
                f'OK: Received valid speed - linear={linear}, angular={angular}'
            )


def main(args=None):
    rclpy.init(args=args)
    node = VelocitySubscriber()

    try:
        rclpy.spin(node)  # 一直监听
    except KeyboardInterrupt:
        pass  # 捕获 Ctrl+C 或 SIGINT 信号
    finally:
        node.destroy_node()  # 清理节点资源
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
