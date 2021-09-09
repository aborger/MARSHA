#include <moveit/move_group_interface/move_group_interface.h>
#include <moveit/planning_scene_interface/planning_scene_interface.h>

#include <moveit_msgs/DisplayRobotState.h>
#include <moveit_msgs/DisplayTrajectory.h>

#include <moveit_msgs/AttachedCollisionObject.h>
#include <moveit_msgs/CollisionObject.h>

#include <moveit_visual_tools/moveit_visual_tools.h>

#include <ros/ros.h>
#include "marsha_ai/Pose.h" // Replace with geometry_msgs/Pose.msg
#include <std_msgs/Empty.h>

#include <vector>

static const std::string PLANNING_GROUP = "manipulator";

class MarshaMoveInterface {
    private:
        moveit::planning_interface::MoveGroupInterface* move_group;
        //const robot_state::JointModelGroup* joint_model_group;
        ros::Subscriber position_sub;
        ros::Subscriber get_pose_sub;

        // Move to pose
        void positionCallBack(const marsha_ai::Pose::ConstPtr& msg)
        {
            ROS_INFO("Taking action[ x: %f y: %f z: %f", msg->pos.x, msg->pos.y, msg->pos.z);
            
            geometry_msgs::Pose target_pose1;
            target_pose1.orientation.w = msg->orient.w;
            target_pose1.orientation.x = msg->orient.x;
            target_pose1.orientation.y = msg->orient.y;
            target_pose1.orientation.z = msg->orient.z;
            target_pose1.position.x = msg->pos.x;
            target_pose1.position.y = msg->pos.y;
            target_pose1.position.z = msg->pos.z;
            move_group->setPoseTarget(target_pose1);

            moveit::planning_interface::MoveGroupInterface::Plan target_plan;

            ROS_INFO("Getting success...");
            bool success = (move_group->plan(target_plan) == moveit::planning_interface::MoveItErrorCode::SUCCESS);
            ROS_INFO("Plan status: %s", success ? "" : "FAILED");
            move_group->move();

        }

        // Return current pose
        void getPose(const std_msgs::Empty::ConstPtr& msg)
        {
            geometry_msgs::Pose pose = move_group->getCurrentPose().pose;
            geometry_msgs::Point position = pose.position;
            geometry_msgs::Quaternion orientation = pose.orientation;

            ROS_WARN("Position [x: %f y: %f z: %f] Orientation [x: %f y: %f z: %f w: %f]", 
                      position.x, position.y, position.z, 
                      orientation.x, orientation.y, orientation.z, orientation.w
            );
        }

    public:
        MarshaMoveInterface(ros::NodeHandle *nh) {
            move_group = new moveit::planning_interface::MoveGroupInterface(PLANNING_GROUP);
            //joint_model_group = move_group->getCurrentState()->getJointModelGroup(PLANNING_GROUP);
            position_sub = nh->subscribe("pos_cmd", 1000, &MarshaMoveInterface::positionCallBack, this);
            get_pose_sub = nh->subscribe("get_state", 1000, &MarshaMoveInterface::getPose, this);
        }

};


int main(int argc, char** argv)
{
    ros::init(argc, argv, "move_interface");
    ros::NodeHandle nh;
    ros::AsyncSpinner spinner(4);
    spinner.start();
    MarshaMoveInterface interface = MarshaMoveInterface(&nh);
    ros::waitForShutdown();
}