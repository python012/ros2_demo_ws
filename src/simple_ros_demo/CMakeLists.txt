cmake_minimum_required(VERSION 3.8)
project(simple_ros_demo)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# 查找依赖
find_package(ament_cmake REQUIRED)
find_package(rclpy REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(std_srvs REQUIRED)
find_package(rosidl_default_generators REQUIRED)

# 生成接口
rosidl_generate_interfaces(${PROJECT_NAME}
  "simple_ros_demo/srv/SetSpeed.srv"
  DEPENDENCIES geometry_msgs std_srvs
)

# 安装 Python 脚本
install(PROGRAMS
  simple_ros_demo/sim_velocity_publisher.py
  simple_ros_demo/velocity_subscriber.py
  simple_ros_demo/speed_service_server.py
  DESTINATION lib/${PROJECT_NAME}
)

# 安装资源
install(DIRECTORY
  simple_ros_demo/srv
  DESTINATION share/${PROJECT_NAME}/
)

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  ament_lint_auto_find_test_dependencies()

  find_package(launch_testing_ament_cmake REQUIRED)
  add_launch_test(test/test_publisher_rate_launch.py TIMEOUT 40)
endif()

ament_package()