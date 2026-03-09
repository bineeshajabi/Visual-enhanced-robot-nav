'''
Author: Bineesha
Date: 14 / 12 /2025

Describer:  Launch the tortoisebot and visualise in RViz
			
'''
from launch_ros.actions import Node
from launch import LaunchDescription
from launch.substitutions import Command,PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare
from launch_ros.parameter_descriptions import ParameterValue

def generate_launch_description():
	
	#Define filenames
	pkg_bot = 'tb3_description'
	urdf_file='robot_define.urdf.xacro'
	rviz_file = 'model_house.rviz'

	#Set the paths
	pkg_descripton = FindPackageShare(pkg_bot)

	urdf_path=PathJoinSubstitution([pkg_descripton,'urdf/burger_tb3',urdf_file])

	rviz_config_file=PathJoinSubstitution([pkg_descripton,'rviz',rviz_file])

	robot_description=ParameterValue(Command([
		'xacro',' ',urdf_path]),
		value_type=str)
	
	# Subscribe to the joint states of the robot, and publish the 3D pose of each link.
	robot_state_publisher_bot=Node(
		package='robot_state_publisher',
		executable='robot_state_publisher',
		name='robot_state_publisher_bot',
		output='screen',
		parameters=[{
			'robot_description':robot_description}]
	)
	
	# Publishes the joint states from URDF file 
	joint_state_publisher_gui_bot=Node(
		package='joint_state_publisher_gui',
		executable='joint_state_publisher_gui',
		name='joint_state_publisher_gui_bot',
		output='screen'		
	)

	#RViz node 
	rviz_bot=Node(
		 executable ='rviz2',
		 name       ='rviz2_bot',
		 output     ='log',
		 arguments  =['-d', rviz_config_file])



	return LaunchDescription([robot_state_publisher_bot, joint_state_publisher_gui_bot, rviz_bot ])

'''

Author: Bineesha
Date: 14 / 12 /2025

Describer:  Launch the tortoisebot and visualise in RViz
			
from launch_ros.actions import Node
from launch import LaunchDescription
from launch.substitutions import Command,PathJoinSubstitution,LaunchConfiguration
from launch_ros.substitutions import FindPackageShare
from launch_ros.parameter_descriptions import ParameterValue
from launch.actions import DeclareLaunchArgument,GroupAction
from launch_ros.actions import PushRosNamespace
from launch.conditions import IfCondition

def generate_launch_description():
	
	#Launching namespace
	namespace = LaunchConfiguration('namepace')
	use_namespace = LaunchConfiguration('use_namespace')

	#Declare the namespace launch argument
	declare_namespace_cmd = DeclareLaunchArgument(
		name='namespace',
		default_value='tb1',
		description='Namespace for the launched nodes'
	)
	declare_use_namespace_cmd = DeclareLaunchArgument(
		name='use_namespace',
		default_value='true',
		description='Whether to apply the namespace to the launched nodes'
	)
	
	#Define filenames
	pkg_bot = 'tortoisebot_description'
	urdf_file='robot_model.urdf.xacro'
	rviz_file = 'robot_bot.rviz'

	#Set the paths
	pkg_descripton = FindPackageShare(pkg_bot)

	urdf_path=PathJoinSubstitution([pkg_descripton,'urdf',urdf_file])

	rviz_config_file=PathJoinSubstitution([pkg_descripton,'rviz',rviz_file])

	robot_description=ParameterValue(Command([
		'xacro',' ',urdf_path]),
		value_type=str)
	
	#To define functions for each robot or namespace
	bringup_grp_code = GroupAction([
		PushRosNamespace(
			condition(IfCondition(use_namespace)),
			namespace=namespace),

			# Subscribe to the joint states of the robot, and publish the 3D pose of each link.
			robot_state_publisher_bot=Node(
				package='robot_state_publisher',
				executable='robot_state_publisher',
				name='robot_state_publisher_bot',
				output='screen',
				parameters=[{
					'robot_description':robot_description}],
				namespaces=[namespace]
			)
			
			# Publishes the joint states from URDF file 
			joint_state_publisher_gui_bot=Node(
				package='joint_state_publisher_gui',
				executable='joint_state_publisher_gui',
				name='joint_state_publisher_gui_bot',
				output='screen',
				namespaces=[namespace]
			)

			#RViz node 
			rviz_bot=Node(
				executable ='rviz2',
				name       ='rviz2_bot',
				output     ='log',
				arguments  =['-d', rviz_config_file],
				namespaces=[namespace]
			)
	])

	return LaunchDescription([declare_namespace_cmd,declare_use_namespace_cmd,bringup_grp_code])
'''