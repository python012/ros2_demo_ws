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
from simple_ros_demo.srv import SetSpeed   # 导入 SetSpeed


class SpeedServiceServer(Node):
    def __init__(self):
        super().__init__('speed_service_server')  # 节点名字
        # 创建服务：服务名 'set_speed'，服务类型 SetSpeed，回调函数 handle_set_speed
        self.srv = self.create_service(SetSpeed, 'set_speed', self.handle_set_speed)
        self.get_logger().info('SetSpeed service server started! Ready at /set_speed')

    def handle_set_speed(self, request, response):
        # request 是客户端发来的目标速度
        target_linear = request.target_linear
        target_angular = request.target_angular

        # 简单校验（和 Subscriber 类似）
        if abs(target_linear) > 2.0 or abs(target_angular) > 1.0:
            response.success = False
            response.message = (
                f'Failed: speed out of range '
                f'(linear={target_linear}, angular={target_angular})'
            )
            self.get_logger().warn(response.message)
        else:
            response.success = True
            response.message = 'Success: speed set!'
            self.get_logger().info(
                f'Set speed: linear={target_linear}, angular={target_angular}'
            )

        # 返回 response 给客户端
        return response


def main(args=None):
    rclpy.init(args=args)
    node = SpeedServiceServer()

    try:
        rclpy.spin(node)  # 一直等待客户端调用
    except KeyboardInterrupt:
        pass  # 捕获 Ctrl+C 或 SIGINT 信号
    finally:
        node.destroy_node()  # 清理节点资源
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
