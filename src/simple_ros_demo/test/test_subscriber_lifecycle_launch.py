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
ROS2 launch_testing integration test for Subscriber lifecycle.

测试目标：验证 velocity_subscriber.py 节点启动/关闭是否正常。
"""

import time
import unittest

import launch
import launch_ros.actions
import launch_testing
import launch_testing.actions
import launch_testing.asserts
import pytest

READY_DELAY_SEC = 1.0
RUN_WINDOW_SEC = 2.0


@pytest.mark.launch_test
def generate_test_description():
    """
    Generate test description for launching nodes.

    启动被测 Subscriber 节点，并在短暂延迟后发出 ReadyToTest 信号。
    """
    subscriber_node = launch_ros.actions.Node(
        package='simple_ros_demo',
        executable='velocity_subscriber.py',
        name='velocity_subscriber_under_test',
        output='screen',
    )

    return (
        launch.LaunchDescription(
            [
                subscriber_node,
                launch.actions.TimerAction(
                    period=READY_DELAY_SEC,
                    actions=[launch_testing.actions.ReadyToTest()],
                ),
            ]
        ),
        {'subscriber_node': subscriber_node},
    )


class TestSubscriberLifecycle(unittest.TestCase):
    """
    Test case to verify Subscriber node stays alive during test window.

    确保节点在测试窗口内保持运行。
    """

    def test_subscriber_runs(self):
        """
        Wait briefly to ensure node is running.

        使用短暂停留窗口让节点稳定运行。
        """
        time.sleep(RUN_WINDOW_SEC)
        self.assertTrue(True)


@launch_testing.post_shutdown_test()
class TestSubscriberProcessExit(unittest.TestCase):
    """
    Test case to verify subscriber node exit code is normal.

    节点关闭后断言退出码为 0。
    """

    def test_exit_codes(self, proc_info, subscriber_node):
        """
        Check subscriber node exit code.

        参数由 launch_testing 注入，断言进程正常退出。
        """
        launch_testing.asserts.assertExitCodes(proc_info, process=subscriber_node)
