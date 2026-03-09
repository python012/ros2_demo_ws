from glob import glob
import os
from setuptools import find_packages, setup

package_name = 'simple_ros_demo'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (
            os.path.join('share', package_name, 'srv'),
            glob(os.path.join('simple_ros_demo', 'srv', '*.srv')),
        ),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='reed',
    maintainer_email='reed@todo.todo',
    description='TODO: Package description',
    license='TODO: License declaration',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'velocity_publisher = simple_ros_demo.sim_velocity_publisher:main',
            'velocity_subscriber = simple_ros_demo.velocity_subscriber:main',
            'speed_service_server = simple_ros_demo.speed_service_server:main',
        ],
    },
)
