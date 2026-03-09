from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch_ros.substitutions import FindPackageShare
from launch_ros.actions import Node
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import PathJoinSubstitution

def generate_launch_description(): 

    pkg_name ='vision_bot'

    pkg_bot=FindPackageShare(pkg_name) 
    
    rviz_file = 'model_house.rviz'
    rviz_config_file=PathJoinSubstitution([pkg_bot,'rviz',rviz_file])

    #RViz node 
    rviz_bot = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2_bot',
        output='log',
        arguments=['-d', rviz_config_file],
        parameters=[{'use_sim_time': True}]
)

    
    slam_map =PathJoinSubstitution([pkg_bot,'config','mapper_params_online_async.yaml'])
    #Slam_toolbox
    slam_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            [PathJoinSubstitution([FindPackageShare('slam_toolbox'),'launch','online_async_launch.py'])]),
                                                            launch_arguments={'slam_params_file':slam_map,
                                                                              'use_sim_time':'true'}.items()     )
                                        
    return LaunchDescription([
        rviz_bot,
        slam_launch
    ])