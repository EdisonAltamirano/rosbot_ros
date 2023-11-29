# Copyright 2023 Husarion
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

from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument, TimerAction
from launch.substitutions import (
    PathJoinSubstitution,
    PythonExpression,
    LaunchConfiguration,
)
from launch.launch_description_sources import PythonLaunchDescriptionSource

from launch_ros.actions import SetParameter

from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
    mecanum = LaunchConfiguration("mecanum")
    declare_mecanum_arg = DeclareLaunchArgument(
        "mecanum",
        default_value="False",
        description=(
            "Whether to use mecanum drive controller (otherwise diff drive controller is used)"
        ),
    )

    world_package = get_package_share_directory("husarion_office_gz")
    world_file = PathJoinSubstitution([world_package, "worlds", "husarion_world.sdf"])
    world_cfg = LaunchConfiguration("world")
    declare_world_arg = DeclareLaunchArgument(
        "world", default_value=world_file, description="SDF world file"
    )

    headless = LaunchConfiguration("headless")
    declare_headless_arg = DeclareLaunchArgument(
        "headless",
        default_value="False",
        description="Run Gazebo Ignition in the headless mode",
    )

    headless_cfg = PythonExpression(
        [
            "'--headless-rendering -s -v 4 -r' if ",
            headless,
            " else '-r -v 4 '",
        ]
    )
    gz_args = [headless_cfg, " ", world_cfg]

    use_gpu = LaunchConfiguration("use_gpu")
    declare_use_gpu_arg = DeclareLaunchArgument(
        "use_gpu",
        default_value="True",
        description="Whether GPU acceleration is used",
    )

    gz_sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution(
                [
                    get_package_share_directory("ros_gz_sim"),
                    "launch",
                    "gz_sim.launch.py",
                ]
            )
        ),
        launch_arguments={
            "gz_args": gz_args,
            "on_exit_shutdown": "True",
        }.items(),
    )

    spawn_robot1_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution(
                [
                    get_package_share_directory("rosbot_gazebo"),
                    "launch",
                    "spawn.launch.py",
                ]
            )
        ),
        launch_arguments={
            "mecanum": mecanum,
            "use_multirobot_system": "True",
            "use_sim": "True",
            "use_gpu": use_gpu,
            "simulation_engine": "ignition-gazebo",
            "namespace": "rosbot1",
            "x": LaunchConfiguration("x1", default="0.00"),
            "y": LaunchConfiguration("y1", default="2.00"),
            "z": LaunchConfiguration("z1", default="0.20"),
            "roll": LaunchConfiguration("roll1", default="0.00"),
            "pitch": LaunchConfiguration("pitch1", default="0.00"),
            "yaw": LaunchConfiguration("yaw1", default="0.00"),
        }.items(),
    )

    spawn_robot2_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution(
                [
                    get_package_share_directory("rosbot_gazebo"),
                    "launch",
                    "spawn.launch.py",
                ]
            )
        ),
        launch_arguments={
            "mecanum": mecanum,
            "use_multirobot_system": "True",
            "use_sim": "True",
            "use_gpu": use_gpu,
            "simulation_engine": "ignition-gazebo",
            "namespace": "rosbot2",
            "x": LaunchConfiguration("x2", default="1.00"),
            "y": LaunchConfiguration("y2", default="2.00"),
            "z": LaunchConfiguration("z2", default="0.20"),
            "roll": LaunchConfiguration("roll2", default="0.00"),
            "pitch": LaunchConfiguration("pitch2", default="0.00"),
            "yaw": LaunchConfiguration("yaw2", default="0.00"),
        }.items(),
    )

    delayed_spawn_robot2 = TimerAction(period=10.0, actions=[spawn_robot2_launch])
    return LaunchDescription(
        [
            declare_mecanum_arg,
            declare_world_arg,
            declare_headless_arg,
            declare_use_gpu_arg,
            # Sets use_sim_time for all nodes started below
            # (doesn't work for nodes started from ignition gazebo)
            SetParameter(name="use_sim_time", value=True),
            gz_sim,
            spawn_robot1_launch,
            delayed_spawn_robot2,
        ]
    )
