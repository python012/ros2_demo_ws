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

"""
ROS2 launch_testing integration test for SetSpeed service behavior.

测试目标：验证 /set_speed 服务的正常响应与异常输入处理。
"""

import time
import unittest

import launch
import launch_ros.actions
import launch_testing
import launch_testing.actions
import launch_testing.asserts
import pytest
import rclpy

SERVICE_TIMEOUT_SEC = 5.0
CALL_TIMEOUT_SEC = 3.0


@pytest.mark.launch_test
def generate_test_description():
    """
    Generate test description for launching nodes.

    启动被测 Service 节点，并在 1 秒后发出 ReadyToTest 信号。
    """
    service_node = launch_ros.actions.Node(
        package='simple_ros_demo',
        executable='speed_service_server.py',
        name='speed_service_server_under_test',
        output='screen',
    )

    return (
        launch.LaunchDescription(
            [
                service_node,
                launch.actions.TimerAction(
                    period=1.0,
                    actions=[launch_testing.actions.ReadyToTest()],
                ),
            ]
        ),
        {'service_node': service_node},
    )


class TestSpeedService(unittest.TestCase):
    """
    Test case to validate SetSpeed service responses.

    覆盖正常输入和超范围输入的服务响应逻辑。
    """

    @classmethod
    def setUpClass(cls):
        """Initialize rclpy before all tests."""
        rclpy.init()

    @classmethod
    def tearDownClass(cls):
        """Shutdown rclpy after all tests."""
        if rclpy.ok():
            rclpy.shutdown()

    def _wait_for_service(self, client):
        deadline = time.monotonic() + SERVICE_TIMEOUT_SEC
        while time.monotonic() < deadline:
            if client.wait_for_service(timeout_sec=0.2):
                return
        self.fail('等待 /set_speed 服务超时')

    def _call_service(self, node, client, linear, angular, SetSpeed):
        request = SetSpeed.Request()
        request.target_linear = float(linear)
        request.target_angular = float(angular)
        future = client.call_async(request)
        rclpy.spin_until_future_complete(node, future, timeout_sec=CALL_TIMEOUT_SEC)
        response = future.result()
        self.assertIsNotNone(response, '服务调用未返回结果')
        return response

    def test_set_speed_service_responses(self):
        """
        Validate SetSpeed service responses for valid and invalid inputs.

        输入合法速度应成功，超范围应失败。
        """
        # 延迟导入：避免在 pytest 收集阶段导入未生成的接口
        from simple_ros_demo.srv import SetSpeed

        node = rclpy.create_node('set_speed_test_client')
        try:
            client = node.create_client(SetSpeed, 'set_speed')
            self._wait_for_service(client)

            ok_response = self._call_service(node, client, 1.0, 0.5, SetSpeed)
            self.assertTrue(ok_response.success, '合法输入应返回 success=True')
            self.assertIn('Success', ok_response.message)

            bad_response = self._call_service(node, client, 3.0, 2.0, SetSpeed)
            self.assertFalse(bad_response.success, '非法输入应返回 success=False')
            self.assertIn('Failed', bad_response.message)
        finally:
            node.destroy_node()


@launch_testing.post_shutdown_test()
class TestSpeedServiceProcessExit(unittest.TestCase):
    """
    Test case to verify service node exit code is normal.

    节点关闭后断言退出码为 0。
    """

    def test_exit_codes(self, proc_info, service_node):
        """
        Check service node exit code.

        参数由 launch_testing 注入，断言进程正常退出。
        """
        launch_testing.asserts.assertExitCodes(proc_info, process=service_node)
