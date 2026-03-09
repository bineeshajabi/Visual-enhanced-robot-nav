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

    tf_static__map_node =Node(
        package= "tf2_ros",
        executable= "static_transform_publisher",
        arguments=
            ['-0.22981178760528564', '0.081793002784252167', '9.6025075912475586',            # translation (x y z)
            '3.1415899979989477', '1.57079000476762', '3.1415899979989477',             # rotation (roll pitch yaw)
            'map',                     #parent frame
            'aerial_rgbd_camera/link', # child frame
            ],
        parameters=[{'use_sim_time': True}]
        )
    

    #RViz node 
    rviz_bot=Node(
		 executable ='rviz2',
		 name       ='rviz2_bot',
		 output     ='log',
		 arguments  =['-d', rviz_config_file],
         parameters=[{'use_sim_time': True}])
    
    slam_map_l =PathJoinSubstitution([FindPackageShare('vision_bot'),'config','mapper_params_localization.yaml'])
    #Slam_toolbox
    slam_launch_l = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            [PathJoinSubstitution([FindPackageShare('slam_toolbox'),'launch','localization_launch.py'])]),
                                                            launch_arguments={'slam_params_file':slam_map_l,
                                                                              'use_sim_time':'true'}.items()
    )
                                  
    return LaunchDescription([
        rviz_bot,
        slam_launch_l,
        tf_static__map_node
    ])