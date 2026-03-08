#!/usr/bin/env python3

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
            self.get_logger().warn(f'WARNING: Invalid speed! linear={linear}, angular={angular}')
        else:
            self.get_logger().info(f'OK: Received valid speed - linear={linear}, angular={angular}')

def main(args=None):
    rclpy.init(args=args)
    node = VelocitySubscriber()
    rclpy.spin(node)          # 一直监听
    rclpy.shutdown()

if __name__ == '__main__':
    main()
