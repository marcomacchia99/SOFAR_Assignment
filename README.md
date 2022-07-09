# Sofar Assignment - [Software architecture for Robotics (2021-2022)](https://corsi.unige.it/off.f/2021/ins/51197) , [Robotics Engineering](https://courses.unige.it/10635).
Tiago Robot simulation using ROS, Rviz and Gazebo.
================================


Introduction
------------

The purpose of this assignment is to develop a software architecture that uses opensource 3D object detection models to allow a robot manipulator to independently estimate the position of a given object (through an RGB-D camera) and potentially grasp it.
In order to verify the simulation in a real environment, given the availability of the Tiago robot in the laboratory, the latter mentioned was selected to carry out the software simulation on Gazebo.


Installing and Running
--------

The simulation is built on the [__ROS__](http://wiki.ros.org) (__Robot-Operating-Systems__) platform, specifically the MELODIC version to be able to have the Tiago Ros package in it. Here the guide for Tiago installation [Tiago robot](http://wiki.ros.org/Robots/TIAGo/Tutorials/Installation/InstallUbuntuAndROS).
To use the melodic version it was necessary to work for the project on __Ubuntu 18__ which can be donwoloaded at [Download Ubuntu 18](https://releases.ubuntu.com/18.04/).

The program requires the installation of the following packages and tools for the specific project before it can be launched:

For the part of the project relating to object recognition, the Mediapipe library was used, thanks to which we were able to simply obtain the identification of a certain object with respect to the robot's camera, in our case we chose the recognition of a cup.
MediaPipe Objectron is a mobile real-time 3D object detection solution for everyday objects. It detects objects in 2D images, and estimates their poses through a machine learning (ML) model.
We found the tutorial and the downloadable packages here:

* [Mediapipe Objectron](https://google.github.io/mediapipe/solutions/objectron)

Another tool needed was the one concerned to the part of moving the robot and grasping the object in the correct way.
__MoveIt__ was chosen for the purpose, a system that provides the necessary trajectories for the arm of a robot to put the end effector in a given place. The wrappers provide functionality for most operations that the average user will likely need, specifically setting joint or pose goals, creating motion plans, moving the robot, adding objects into the environment and attaching/detaching objects from the robot.

* [MoveIt](http://docs.ros.org/en/melodic/api/moveit_tutorials/html/index.html)
 
Easy to install with:

```bash
	$ sudo apt install ros-melodic-moveit
```
Also, in order to correctly run the simulation, you have to install the following packages:

* python3-rospkg
* ros-numpy
* scipy 

Finally, to launch the simulation, you should run this .launch file:

```bash
	$ roslaunch SOFAR_Assignment launcher.launch
```


Environment
--------

As soon as the simulation starts, Gazebo (an open-source 3D Robotics simulator) appears on the screen.

We used the Gazebo environment to control the right movement of the robot's joints and to verify the correct functioning of the code within a real simulation world.
ROS creates the scenario described in the __world__ folder, regarding to this we have built an environment called `table_and_cup.world` where the robot spawns and in front of him you can find a table with a cup on it.


<p align="center">
    
<img src="https://github.com/marcomacchia99/SOFAR_Assignment/blob/master/assets/Tiago_spawn.jpg" width="600" >
    
</p>


Implementation choices
--------------
First of all, the purpose of the assignment was not a simple matter to deal with and we thought it was not the best idea to use a single script of code. We therefore decided to separate the things in order to achieve the goal of having a more modular code.

Then, the approach used was the more general that we could to better obtain as a final result, a robot which can adjust its position depending on the object 
coordinates in the space (however the object must remain in the range of the robot camera).

Another thing to face up with was that the Objectron tool from Mediapipe returns the frames and coordinates of the robot camera frame, more in specific the xtion_rgb_frame, so we had to dedicate a whole node to extract the relative pose of the object with respect to the camera and with the correct transformations, thanks to tf package functions, have the pose of the object with respect to the base frame (base_footprint) of the robot.

To achieve the final change of coordinates it was necessary to pass through the quaternions as regards the orientation of the object, and then multiply them thanks to the appropriate function `quaternion_multiply` with the corresponding component of each coordinate.

Object Recognition
------

It was decided to implement a single node that provided the recognition of an object as soon as it was displayed within the visual range of the camera of the Tiago robot. In order to achieve it, firstly we imported the needed libraries for our aim, such as `ros_numpy`, `mediapipe`, `sensor_msgs` to import from the robot sensors the image seen from the camera and from `geometry_msgs` the object Pose, useful to extrapolate the position with `Point` and the orientation in quaternions. 

To obtain in the right way the rotation matrix we just pass through the __scipy__ open source library that could extract and import the orientation of the object with respect to the robot camera frame.

At this point we made up the _recognize_ function that takes in input the image which is taken from the subscription to the `/xtion/rgb/image_raw` topic.
Now there is the definition of the object takes place via mediapipe as objectron, as shown below:

```python
with mp_objectron.Objectron(
            static_image_mode=False,
            max_num_objects=1,
            min_detection_confidence=0.5,
            model_name='Cup') as objectron:
```

Then we converted the BGR image to RGB and process it with MediaPipe Objectron with `objectron.process(ros_numpy.numpify(image))` and, if the object is detected, we printed out a log message for real-time feedback.

Another matter was to use the quaternions to work properly in ROS with rotation matrices. For this reason scipy library was used, which provides the orientation as a rotation matrix and then it can be convertible to the quaternion format.
The compact command used is the following:

```python
q = R.from_matrix(results.detected_objects[0].rotation).as_quat()
```

Finally we ended up the node with the publishers to the '/sofar/target_pose/relative' and the '/sofar/target_pose/relative/stamped' for the Pose and PoseStamped topic for rispectively publish the correct relative position of the coordinate frame of the object with respect to the robot camera frame and the other was used to visualize it on RViz to have an extra feedback.

Object change of coordinates to base frame
-------

As already mentioned, the coordinates taken from the geometry_msgs topic are with respect to the camera frame of the Tiago robot. It is therefore necessary, through a transformation, to make a change of coordinates to pass to the reference system with respect to the base frame. To do this we used tf2 package to have the right transformation.

We made up the __RelToAbsolute__ service which is build with this structure:


*geometry_msgs/PoseStamped relative_pose*

*---*

*geometry_msgs/PoseStamped absolute_pose*


Then we used a specific function which gets the transform between two frames by frame ID assuming fixed frame:

```python
tfBuffer.lookup_transform('base_footprint', rel_pose.relative_pose.header.frame_id, rospy.Time())
```

Once the transformation was obtained, the `do_transform_point` function was used to pass from the cartesian cordinates with respect to the camera frame to the *base footprint* frame, corresponding to the base frame, the one attached to the base of the robot. 

As previously done, the last thing to do is to pass into the quaternion domain to work in the format that ROS wants.
This is simply made by the function `quaternion_multiply` which makes the change of coordinates multiplicating the two quaternions previously built with the coordinates components regarding the relative pose to the camera frame and the ones relative to the transformation.

In the end we have built up the final absolute pose with respect to the base frame and returned printing it.

Robot grasp
------

For the part concerning the grasping movement, two nodes have been implemented that deal specifically with that: one regarding the real final approach to the object and picking it (`pickObject.py`) and one about what the robot do when the simulation starts, so the various actions before the grab and after that (`pickClient.py`).

### Pick client

As already mentioned, this node deals with managing the movements of the robot when the simulation begins. To do this we used the __SimpleActionClient__ library to use [PlayMotion](http://wiki.ros.org/Robots/TIAGo/Tutorials/motions/play_motion), thanks to which we were able to send a goal to reach a certain position with an adequate configuration of the robot's joints and then perform a certain action; we used trajectory_msgs.msg package that defines messages for pointing out robot trajectories, so to adjust some movements more accurately or to make the robot move specific parts, such as the head to find the object; an __ApproachObject__ service created by us as follows:

*geometry_msgs/Pose pose*

*---*

*bool result*


More in specific we have implemented some functions that were necessary to make Tiago perform some actions.

As soon as the node is launched, thanks to SimpleActionClient we can send a goal with __PlayMotionGoal__, using the send_goal_and_wait function.
First we send the robot to the home position, then we managed to publish to the `JointTrajectory` topic in order to be able to change the configuration of the joints, in particular, for now, we just wnat to move the Tiago's head to find the object which is on the table. After that we subscribe to the `/sofar/target_pose/relative` to pick the relative position of the object.

At this point we have defined the move_head() function that has precisely the purpose previously stated: look down for the object on the table.



### Pick object


Rqt graph
------
The project graph, which illustrates the relationships between the nodes, is shown below. Keep in mind that this is a graph built by executing all the nodes at the same time in order to obtain a full graph.

The graph can be generated using this command:
 
```console
$ rqt_graph
``` 

<p align="center">
    
<img src="https://github.com/marcomacchia99/SOFAR_Assignment/blob/master/assets/rosgraph.png" width="600" >
    
</p>




Flowchart (?)
-------


Simulation
-------


Conclusions and possible future improvements
--------------


