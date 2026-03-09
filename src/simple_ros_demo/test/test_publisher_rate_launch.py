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
ROS2 launch_testing integration test for Publisher rate validation.

测试目标：检查 sim_velocity_publisher.py 节点发布 /cmd_vel 的频率是否符合 10Hz ± 2Hz。
测试方法：启动节点 -> 订阅话题收集时间戳 -> 计算实际频率 -> 断言是否在范围内。
"""

import statistics
import time
import unittest

import launch
import launch_ros.actions
import launch_testing
import launch_testing.actions
import launch_testing.asserts
import pytest
import rclpy
from geometry_msgs.msg import Twist
from rclpy.node import Node

TARGET_RATE_HZ = 10.0
RATE_TOLERANCE_HZ = 2.0
MIN_RATE_HZ = TARGET_RATE_HZ - RATE_TOLERANCE_HZ
MAX_RATE_HZ = TARGET_RATE_HZ + RATE_TOLERANCE_HZ
SAMPLES_TO_COLLECT = 35
WARMUP_INTERVALS_TO_DROP = 5


@pytest.mark.launch_test
def generate_test_description():
    """
    Generate test description for launching nodes.

    启动被测 Publisher 节点，并在 1 秒后发出 ReadyToTest 信号。
    """
    publisher_node = launch_ros.actions.Node(
        package='simple_ros_demo',
        executable='sim_velocity_publisher.py',
        name='velocity_publisher_under_test',
        output='screen',
    )

    return (
        launch.LaunchDescription(
            [
                publisher_node,
                launch.actions.TimerAction(
                    period=1.0,
                    actions=[launch_testing.actions.ReadyToTest()],
                ),
            ]
        ),
        {'publisher_node': publisher_node},
    )


class _RateProbe(Node):
    """
    Rate probe node for measuring message frequency on /cmd_vel.

    临时测试节点，只记录收到消息时的时间戳，不处理消息内容。
    """

    def __init__(self):
        super().__init__('cmd_vel_rate_probe')
        self.timestamps = []
        self.subscription = self.create_subscription(
            Twist,
            '/cmd_vel',
            self._callback,
            10,
        )

    def _callback(self, _msg):
        """
        Record timestamp when a message is received.

        使用 monotonic 时钟，避免系统时间跳变影响统计结果。
        """
        self.timestamps.append(time.monotonic())


class TestPublisherRate(unittest.TestCase):
    """
    Test case to verify Publisher rate is close to 10Hz ± 2Hz.

    收集样本后计算稳定阶段平均周期，并换算频率进行断言。
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

    def test_cmd_vel_publish_rate_is_near_10hz(self):
        """
        Verify /cmd_vel publish rate is close to 10Hz.

        在 8 秒窗口中收集样本，并断言频率位于 [8Hz, 12Hz]。
        """
        probe = _RateProbe()

        deadline = time.monotonic() + 8.0
        try:
            while (
                time.monotonic() < deadline
                and len(probe.timestamps) < SAMPLES_TO_COLLECT
            ):
                rclpy.spin_once(probe, timeout_sec=0.2)
        finally:
            probe.destroy_node()

        self.assertGreaterEqual(
            len(probe.timestamps),
            SAMPLES_TO_COLLECT,
            (
                f'样本不足：只收集到 {len(probe.timestamps)} 条消息，'
                f'需要 {SAMPLES_TO_COLLECT} 条'
            ),
        )

        intervals = [
            probe.timestamps[i + 1] - probe.timestamps[i]
            for i in range(len(probe.timestamps) - 1)
        ]

        stable_intervals = intervals[WARMUP_INTERVALS_TO_DROP:]

        self.assertGreaterEqual(
            len(stable_intervals),
            10,
            '预热后的稳定样本不足，无法准确估算频率',
        )

        mean_period = statistics.mean(stable_intervals)
        measured_rate_hz = 1.0 / mean_period

        self.assertGreaterEqual(
            measured_rate_hz,
            MIN_RATE_HZ,
            (
                f'发布频率过低：实测 {measured_rate_hz:.2f}Hz，'
                f'期望 >= {MIN_RATE_HZ:.2f}Hz'
            ),
        )
        self.assertLessEqual(
            measured_rate_hz,
            MAX_RATE_HZ,
            (
                f'发布频率过高：实测 {measured_rate_hz:.2f}Hz，'
                f'期望 <= {MAX_RATE_HZ:.2f}Hz'
            ),
        )


@launch_testing.post_shutdown_test()
class TestPublisherProcessExit(unittest.TestCase):
    """
    Test case to verify node exit code is normal.

    节点关闭后断言退出码为 0，防止异常退出被忽略。
    """

    def test_exit_codes(self, proc_info, publisher_node):
        """
        Check Publisher node exit code.

        参数由 launch_testing 注入，断言 publisher 进程正常退出。
        """
        launch_testing.asserts.assertExitCodes(proc_info, process=publisher_node)
