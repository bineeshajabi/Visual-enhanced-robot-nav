from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch_ros.substitutions import FindPackageShare
from launch_ros.actions import Node
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import PathJoinSubstitution

def generate_launch_description(): 
    
    pkg_name ='vision_bot'

    pkg_bot=FindPackageShare(pkg_name) 
    
    nav_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            [PathJoinSubstitution([pkg_bot,'launch','navigation.launch.py'])]),
                                                            launch_arguments={'use_sim_time':'true'}.items()
                                                        )
    
    return LaunchDescription([
        nav_launch
    ])