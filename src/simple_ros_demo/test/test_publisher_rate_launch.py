# Copyright 2026
# Licensed under the Apache License, Version 2.0

"""ROS2 launch_testing integration test for Publisher rate validation.

测试目标：检查 sim_velocity_publisher.py 节点发布 /cmd_vel 的频率是否符合 10Hz ± 2Hz
测试方法：启动节点 → 订阅话题收集时间戳 → 计算实际频率 → 断言是否在范围内
"""

import statistics  # 用于计算平均值
import time        # 用于记录时间戳
import unittest    # Python 标准单元测试框架

import launch                        # ROS2 launch 系统
import launch_ros.actions            # ROS2 节点启动工具
import launch_testing                # launch_testing 核心
import launch_testing.actions        # 测试动作（如 ReadyToTest）
import launch_testing.asserts        # 测试断言工具
import pytest                        # pytest 测试框架
import rclpy                         # ROS2 Python 客户端库
from geometry_msgs.msg import Twist  # 速度消息类型
from rclpy.node import Node          # ROS2 节点基类

# ========== 测试参数配置 ==========
TARGET_RATE_HZ = 10.0          # 目标发布频率：10Hz（即每 0.1 秒发布一次）
RATE_TOLERANCE_HZ = 2.0        # 允许的频率偏差：±2Hz
MIN_RATE_HZ = TARGET_RATE_HZ - RATE_TOLERANCE_HZ  # 最小可接受频率：8Hz
MAX_RATE_HZ = TARGET_RATE_HZ + RATE_TOLERANCE_HZ  # 最大可接受频率：12Hz
SAMPLES_TO_COLLECT = 35        # 需要收集的消息样本数（样本越多，统计越准确）
WARMUP_INTERVALS_TO_DROP = 5   # 丢弃的预热样本数（节点启动时前几次发布可能不稳定）


@pytest.mark.launch_test  # 标记为 launch_testing 测试用例
def generate_test_description():
    """Generate test description for launching nodes.

    这个函数会在测试开始前被 launch_testing 框架调用，用于：
    1. 启动被测节点（Publisher）
    2. 设置测试就绪条件（等待 1 秒让节点完全启动）
    3. 返回 LaunchDescription 和节点句柄供后续测试使用
    """
    # 定义要测试的 Publisher 节点
    publisher_node = launch_ros.actions.Node(
        package='simple_ros_demo',              # ROS2 包名
        executable='sim_velocity_publisher.py',  # 可执行文件名（Python 脚本）
        name='velocity_publisher_under_test',    # 给节点起个测试专用名字
        output='screen',                         # 将节点日志输出到屏幕（便于调试）
    )

    return (
        # 第一个返回值：LaunchDescription（描述如何启动节点）
        launch.LaunchDescription(
            [
                publisher_node,  # 添加 Publisher 节点到启动列表
                # 定时器动作：等待 1 秒后触发 ReadyToTest（确保节点完全启动）
                launch.actions.TimerAction(
                    period=1.0,  # 延迟 1 秒
                    actions=[launch_testing.actions.ReadyToTest()],  # 发送"测试就绪"信号
                ),
            ]
        ),
        # 第二个返回值：字典，包含节点句柄（供 post_shutdown_test 使用）
        {'publisher_node': publisher_node},
    )


class _RateProbe(Node):
    """Rate probe node for measuring message frequency on /cmd_vel.

    这是一个临时测试节点，专门用于收集消息时间戳以计算发布频率。
    它不关心消息内容，只记录消息到达的精确时间。
    """

    def __init__(self):
        super().__init__('cmd_vel_rate_probe')  # 节点名：cmd_vel_rate_probe
        self.timestamps = []  # 存储所有消息的时间戳列表

        # 创建订阅者：订阅 /cmd_vel 话题
        self.subscription = self.create_subscription(
            Twist,           # 消息类型：geometry_msgs/Twist
            '/cmd_vel',      # 话题名
            self._callback,  # 回调函数：每收到一条消息就调用
            10,              # 队列大小：最多缓存 10 条消息
        )

    def _callback(self, _msg):
        """Record timestamp when a message is received.

        参数 _msg：接收到的 Twist 消息（这里不关心内容，所以加下划线表示未使用）
        功能：记录当前时间戳到 timestamps 列表
        """
        # 使用 monotonic 时钟（单调递增，不受系统时间调整影响）
        self.timestamps.append(time.monotonic())



class TestPublisherRate(unittest.TestCase):
    """Test case to verify Publisher rate is close to 10Hz ± 2Hz.

    测试流程：
    1. 初始化 rclpy
    2. 创建探测节点订阅 /cmd_vel
    3. 收集 35 个消息样本
    4. 计算平均发布周期和频率
    5. 断言频率是否在 8Hz ~ 12Hz 范围内
    """

    @classmethod
    def setUpClass(cls):
        """Initialize rclpy before all tests."""
        rclpy.init()  # 初始化 ROS2 Python 客户端库

    @classmethod
    def tearDownClass(cls):
        """Shutdown rclpy after all tests."""
        if rclpy.ok():  # 如果 rclpy 还在运行
            rclpy.shutdown()  # 关闭 rclpy，清理资源

    def test_cmd_vel_publish_rate_is_near_10hz(self):
        """Verify /cmd_vel publish rate is close to 10Hz.

        步骤：
        1. 创建探测节点
        2. 循环接收消息直到收集够样本或超时
        3. 计算消息间隔时间
        4. 丢弃预热样本，计算稳定阶段的平均频率
        5. 断言频率是否在允许范围内
        """
        # 创建频率探测节点
        probe = _RateProbe()

        # 设置 8 秒的收集时间上限（避免无限等待）
        deadline = time.monotonic() + 8.0
        try:
            # 循环条件：未超时 且 样本数未达标
            while time.monotonic() < deadline and len(probe.timestamps) < SAMPLES_TO_COLLECT:
                # spin_once：处理一次回调（接收一条消息），超时 0.2 秒
                rclpy.spin_once(probe, timeout_sec=0.2)
        finally:
            # 无论成功失败，都要清理节点（避免资源泄漏）
            probe.destroy_node()

        # ===== 断言1：检查是否收集到足够的样本 =====
        self.assertGreaterEqual(
            len(probe.timestamps),
            SAMPLES_TO_COLLECT,
            f'样本不足：只收集到 {len(probe.timestamps)} 条消息，需要 {SAMPLES_TO_COLLECT} 条',
        )

        # ===== 计算消息间隔时间 =====
        # 相邻两条消息的时间差列表（如果有 35 个时间戳，会得到 34 个间隔）
        intervals = [
            probe.timestamps[i + 1] - probe.timestamps[i]
            for i in range(len(probe.timestamps) - 1)
        ]

        # ===== 丢弃预热样本，保留稳定阶段的间隔 =====
        # 前 5 个间隔可能因为节点启动开销而不稳定，丢弃它们
        stable_intervals = intervals[WARMUP_INTERVALS_TO_DROP:]
        
        # ===== 断言2：检查稳定样本是否足够（至少 10 个） =====
        self.assertGreaterEqual(
            len(stable_intervals),
            10,
            '预热后的稳定样本不足，无法准确估算频率',
        )

        # ===== 计算平均发布周期和频率 =====
        mean_period = statistics.mean(stable_intervals)  # 平均消息间隔（秒）
        measured_rate_hz = 1.0 / mean_period             # 频率 = 1 / 周期（Hz）

        # ===== 断言3：检查频率是否不低于最小值 =====
        self.assertGreaterEqual(
            measured_rate_hz,
            MIN_RATE_HZ,
            f'发布频率过低：实测 {measured_rate_hz:.2f}Hz，期望 >= {MIN_RATE_HZ:.2f}Hz',
        )
        
        # ===== 断言4：检查频率是否不高于最大值 =====
        self.assertLessEqual(
            measured_rate_hz,
            MAX_RATE_HZ,
            f'发布频率过高：实测 {measured_rate_hz:.2f}Hz，期望 <= {MAX_RATE_HZ:.2f}Hz',
        )



@launch_testing.post_shutdown_test()  # 标记为后置测试（节点关闭后执行）
class TestPublisherProcessExit(unittest.TestCase):
    """Test case to verify node exit code is normal.

    这个测试会在所有节点关闭后运行，检查节点是否正常退出（退出码为 0）。
    如果节点崩溃或被强制杀死，退出码会是非零值，测试会失败。
    """

    def test_exit_codes(self, proc_info, publisher_node):
        """Check Publisher node exit code.

        参数：
        - proc_info: 进程信息对象（由 launch_testing 自动注入）
        - publisher_node: Publisher 节点句柄（来自 generate_test_description 返回的字典）

        断言：节点退出码为 0（正常退出）
        """
        # 断言指定进程的退出码为 0（正常退出）
        launch_testing.asserts.assertExitCodes(proc_info, process=publisher_node)

