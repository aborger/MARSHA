#ifndef ARM2D2_HARDWARE_INTERFACE_H
#define ARM2D2_HARDWARE_INTERFACE_H

#include <ros/ros.h>
#include <hardware_interface/joint_state_interface.h>
#include <hardware_interface/joint_command_interface.h>
#include <hardware_interface/robot_hw.h>
#include <string.h>

#include <std_msgs/Int16.h>


#define NUM_JOINTS 7

class MarshaArm : public hardware_interface::RobotHW 
{
    public:
        MarshaArm(ros::NodeHandle &nh_);
        ~MarshaArm();

        void read();
        void write();
        void update(const ros::TimerEvent &e);

        //void encoderCallBack(const std_msgs::Int16MultiArray &msg);
        //void graspCallBack(const std_msgs::Bool &msg);
    private:
        ros::NodeHandle nh;
        ros::Publisher j0_step_pub;
        ros::Publisher j1_step_pub;
        ros::Publisher j2_step_pub;
        ros::Publisher j3_step_pub;
        ros::Publisher j4_step_pub;
        ros::Publisher grip_pub;
        
        //ros::Subscriber grip_sub;


        hardware_interface::JointStateInterface joint_state_interface;
        hardware_interface::PositionJointInterface joint_position_interface;
        hardware_interface::EffortJointInterface joint_effort_interface;
        double cmd[NUM_JOINTS];

        double pos[NUM_JOINTS];
        double vel[NUM_JOINTS];
        double eff[NUM_JOINTS];


        



        std::string joint_names[NUM_JOINTS] = {
            "joint_1",
            "joint_2",
            "joint_3",
            "joint_4",
            "joint_5",
            "gripper_joint",
        };

        double radToDeg(double rad);
        double degToRad(double deg);
};

#endif