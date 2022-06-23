#!/usr/bin/env python3

import rospy
from geometry_msgs.msg import Pose, Twist
import math
from play_motion_msgs.msg import PlayMotionAction, PlayMotionGoal
from nav_msgs.msg import Odometry
from actionlib import SimpleActionClient
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint

global action_client
global pub_head_controller
global sub_target_rel_pose
global head_2_movement
global object_found
global pmgoal
global count
global displacement


def go_to_home_position():
    global action_client
    global pmgoal

    rospy.loginfo("Go into the home position")

    pmgoal = PlayMotionGoal()
    pmgoal.motion_name = 'home'
    pmgoal.skip_planning = False

    action_client.send_goal_and_wait(pmgoal)

    rospy.loginfo("Done.")


def move_head():
    global pub_head_controller
    global head_2_movement
    global object_found

    rospy.loginfo("Moving head")

    while not object_found:

        trajectory = JointTrajectory()
        trajectory.joint_names = ['head_1_joint', 'head_2_joint']

        trajectory_points = JointTrajectoryPoint()
        trajectory_points.positions = [0.0, head_2_movement]
        trajectory_points.time_from_start = rospy.Duration(1.0)

        trajectory.points.append(trajectory_points)

        pub_head_controller.publish(trajectory)

        rospy.sleep(0.8)
        head_2_movement = max(-1, head_2_movement-0.1)

    rospy.loginfo("Done.")

def stop_head_motion(msg):
    global object_found
    global sub_target_rel_pose
    global count

    # count is used to make sure that all the object fits the camera.
    # In order to ensure this, seen the object recognition frequency,
    # the object has to be found for at least 20 times
    count += 1
    if count == 20:
        object_found = True
        sub_target_rel_pose.unregister()    

def prepare_robot():
    global action_client
    global pmgoal

    rospy.loginfo("Go into the initial position")

    pmgoal = PlayMotionGoal()
    pmgoal.motion_name = 'pregrasp'
    pmgoal.skip_planning = False

    action_client.send_goal_and_wait(pmgoal)

    rospy.loginfo("Done.")    


def adjust_position():

    global displacement

    pub_vel = rospy.Publisher(
        '/mobile_base_controller/cmd_vel', Twist, queue_size=1)

    velocity = Twist()

    for i in range(21):
        velocity.angular.z = -math.pi/4
        pub_vel.publish(velocity)
        rospy.sleep(0.1)

    velocity.angular.z = 0
    pub_vel.publish(velocity)
    rospy.sleep(1)

    for i in range(round(displacement/0.25)*10):
        velocity.linear.x = 0.25
        pub_vel.publish(velocity)
        rospy.sleep(0.1)

    velocity.linear.x = 0
    pub_vel.publish(velocity)
    rospy.sleep(1)


    for i in range(20):
        velocity.angular.z = math.pi/4
        pub_vel.publish(velocity)
        rospy.sleep(0.1)

    velocity.angular.z = 0
    pub_vel.publish(velocity)
    rospy.sleep(1)



if __name__ == '__main__':

    rospy.init_node('InitPosition')

    action_client = SimpleActionClient('/play_motion', PlayMotionAction)

    if not action_client.wait_for_server(rospy.Duration(20)):
        rospy.logerr("Could not connect to /play_motion AS")
        exit()

    pmgoal = PlayMotionGoal()

    go_to_home_position()

    pub_head_controller = rospy.Publisher(
        '/head_controller/command', JointTrajectory, queue_size=1)

    sub_target_rel_pose = rospy.Subscriber(
        '/sofar/target_pose/relative', Pose, stop_head_motion)

    head_2_movement = 0
    object_found = False
    count = 0
    displacement = 0 #displacement fittizio, va calcolato


    move_head()


    if displacement>0:
        adjust_position()

    prepare_robot()



    # calcolare displacement con matrice assoluta (la possiamo prendere da quando abbassa la testa e inviare tramite service alla abs)
    # dopo pre grasp basta andare avanti di 0.15 lentamente
    #trasformare getAbsolutePose in servizio, dobbiamo vedere dove metterlo (guardiamo la struttura della pick & place demo)
