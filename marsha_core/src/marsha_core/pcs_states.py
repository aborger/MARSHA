#!/usr/bin/env python


import rospy
import smach
import smach_ros

from marsha_core.pcs_node import PCSstate
from marsha_core.pcs_node import PCScmd

from marsha_core.marsha_services.move_cmds import *
from marsha_core.marsha_services.gripper_cmds import *

CATCH_NA = "C_NA"
CATCH_PENDING = "C_PEND"
CATCH_SUCCESS = "C_1"
CATCH_FAIL = "C_0"
# replace with other_arm_ns
other_arm = None
if rospy.get_namespace() == "/left/":
    other_arm = "/right/"
else:
    other_arm = "/left/"
# ---------------------------------------------------------------- #
#                      Move State Templates                        #
# ---------------------------------------------------------------- #

class Move_State(smach.State):
    def __init__(self):
        smach.State.__init__(self, outcomes=['Success', 'Error'])

class Joint_Pose_State(smach.State):
    def __init__(self, pose):
        smach.State.__init__(self, outcomes=['Success', 'Error'])
        self.pose = pose

    def execute(self, userdata):
        complete = joint_pose_cmd(self.pose).done

        if complete:
            return 'Success'
        else:
            return 'Error'

""" 
Joint_Pose_State Example:

    smach.StateMachine.add('Pre_Throw', Joint_Pose_State("pre_throw"),
                        transitions={'Success': 'Jetson_Sync_1',
                                    'Error': 'Ball_Status'})

"""

class Async_Joint_Pose_State(smach.State):
    def __init__(self, pose):
        smach.State.__init__(self, outcomes=['Success', 'Error'])
        self.pose = pose

    def execute(self, userdata):
        complete = async_joint_pose_cmd(self.pose).done

        if complete:
            return 'Success'
        else:
            return 'Error'

class Grasp_Cmd_State(smach.State):
    def __init__(self, pose):
        smach.State.__init__(self, outcomes=['Success', 'Error'])
        self.pose = pose

    def execute(self, userdata):
        complete = grasp_cmd(self.pose).done

        if complete:
            return 'Success'
        else:
            return 'Error'

# wait_time is in seconds
class Wait_State(smach.State):
    def __init__(self, wait_time):
        smach.State.__init__(self, outcomes=['Complete'])
        self.wait_time = wait_time

    def execute(self, userdata):
        rospy.sleep(self.wait_time)

        return 'Complete'


# ---------------------------------------------------------------- #
#                      Jetson Comm States                          #
# ---------------------------------------------------------------- #

class Check_Catch(smach.State):
    def __init__(self, timeout=10, poll_period=0.5):
        smach.State.__init__(self, outcomes=['Caught', 'Missed', 'Timeout', 'Not_Catching'])

        self.timeout = timeout
        self.poll_period = poll_period

    def execute(self, userdata):
        time_elapsed = 0

        # only so other arm doesnt think this arm is still throwing
        rospy.set_param('sync_id', CATCH_PENDING)

        # waits until other arm has catch feedback
        rospy.loginfo("(JET COMM): Waiting for Catch Status...")
        while rospy.get_param(other_arm + 'sync_id') == CATCH_PENDING:
            rospy.sleep(self.poll_period)
            time_elapsed += self.poll_period
            if time_elapsed > self.timeout:
                return 'Timeout'

        catch_status = rospy.get_param(other_arm + 'sync_id')
        if catch_status == CATCH_NA:
            return 'Not_Catching'
        elif catch_status == CATCH_SUCCESS:
            return 'Caught'
        elif catch_status == CATCH_FAIL:
            return 'Missed'

        # Reset parameter
        rospy.set_param(other_arm + 'catch_status', CATCH_NA)

        

        return 'Ready'

class Ball_Status(smach.State):
    def __init__(self, other_arm_status=False):
        smach.State.__init__(self, outcomes=['2', '1', '0'])

        self.check_other_arm = other_arm_status

        if self.check_other_arm:
            self.balls_remaining_param = other_arm + 'balls_remaining'
        else:
            self.balls_remaining_param = 'balls_remaining'

    def execute(self, userdata):
        balls_remaining = rospy.get_param(self.balls_remaining_param)

        if balls_remaining < 0:
            balls_remaining = 0
            


        return str(balls_remaining)



class Jetson_Comm_Check(smach.State):
    def __init__(self, check_connection):
        smach.State.__init__(self, outcomes=['Success', 'Error'])

        self.check_connection = check_connection

    def execute(self, userdata):
        if self.check_connection():
            rospy.loginfo("Jets Connected!")
            return 'Success'
        else:
            return 'Error'

class Jetson_Sync(smach.State):
    def __init__(self, sync_id, timeout=10, poll_period=0.5): # timeout in seconds
        smach.State.__init__(self, outcomes=['Ready', 'Timeout'])

        self.sync_id = sync_id
        self.timeout = timeout
        self.poll_period = poll_period


    def execute(self, userdata):
        rospy.loginfo("Syncing Jets...")

        time_elapsed = 0
        other_sync_param = other_arm + 'sync_id'

        rospy.set_param('sync_id', self.sync_id)

        # waits until other jetson is on the same state
        rospy.loginfo("(JET COMM): Waiting for Handshake...")
        while rospy.get_param(other_sync_param) != self.sync_id:
            rospy.loginfo("ID: " + str(self.sync_id) + " other ID: " + str(rospy.get_param(other_sync_param)))
            # add something to detect if self.jet_comm() returns False which indicates it cannot communicate with other jetson
            rospy.sleep(self.poll_period)
            time_elapsed += self.poll_period
            if time_elapsed > self.timeout:
                return 'Timeout'

        return 'Ready'

# ---------------------------------------------------------------- #
#                           Complex Moves                          #
# ---------------------------------------------------------------- #
# Note: These are not really used any more
class Home(Move_State):

    def execute(self, userdata):
        joint_pose_cmd("home")
        grasp_cmd("close")

        return 'Success'

class Latch(Move_State):

    def execute(self, userdata):
        grasp_cmd("half_closed")
        joint_pose_cmd("home")
        grasp_cmd("close")

        return 'Success'

class Step_0(Move_State):
    def execute(self, userdata):
        grasp_cmd("half_closed")
        joint_pose_cmd("folding/step_0")

        return "Success"

class Catch(smach.State):
    def __init__(self):
        smach.State.__init__(self, outcomes=['Success', 'Fail'])

    def execute(self, userdata):
        rospy.set_param('sync_id', CATCH_PENDING)
        rospy.sleep(0.75)
        grasp_cmd("close")

        rospy.sleep(1)

        # this is replaced with is_grasped()
        if False:
            rospy.set_param('sync_id', CATCH_SUCCESS)
            return 'Success'
        else:
            rospy.set_param('sync_id', CATCH_FAIL)
            return 'Fail'


class Open_Gripper(Move_State):
    def execute(self, userdata):
        grasp_cmd("open")
        rospy.sleep(1)
        return 'Success'

# should move to state machine
class Pickup_1(Move_State):
    def execute(self, userdata):
        grasp_cmd("half_closed")
        joint_pose_cmd("pre_ball_1")
        joint_pose_cmd("pick_ball_1")
        grasp_cmd("close")
        joint_pose_cmd("pre_ball_1")
        joint_pose_cmd("folding/step_0")

        rospy.sleep(1)

        balls_remaining = rospy.get_param('balls_remaining')
        rospy.set_param('balls_remaining', balls_remaining-1)
        if is_grasped().success:
            # decrease number of balls
            return 'Success'
        else:
            rospy.logwarn("Ball was not picked up!")
            return 'Error'


# should move to state machine
class Pickup_2(Move_State):
    def execute(self, userdata):
        grasp_cmd("half_closed")
        joint_pose_cmd("pre_ball_2")
        joint_pose_cmd("pick_ball_2")
        grasp_cmd("close")
        joint_pose_cmd("pre_ball_2")
        joint_pose_cmd("folding/step_0")

        rospy.sleep(1)

        balls_remaining = rospy.get_param('balls_remaining')
        rospy.set_param('balls_remaining', balls_remaining-1)
        if is_grasped().success:
            # decrease number of balls
            return 'Success'
        else:
            rospy.logwarn("Ball was not picked up!")
            return 'Error'







# ---------------------------------------------------------------- #
#                      Maneuver State Machines                     #
# ---------------------------------------------------------------- #

NUM_FOLDING_STEPS = 5

# ================================================================ #


Unfold_SM = smach.StateMachine(outcomes=["Success", "Fail"])

with Unfold_SM:

    for i in range(0, NUM_FOLDING_STEPS):
        smach.StateMachine.add('step_' + str(i), Joint_Pose_State("folding/step_" + str(i)),
                            transitions={'Success': 'step_' + str(i+1),
                                        'Error': 'Fail'})

    smach.StateMachine.add('step_' + str(NUM_FOLDING_STEPS), Joint_Pose_State("folding/step_" + str(NUM_FOLDING_STEPS)),
                        transitions={'Success': 'Success',
                                     'Error': 'Fail'})


# ================================================================ #

Fold_SM = smach.StateMachine(outcomes=["Success", "Fail"])

with Fold_SM:

    smach.StateMachine.add('Close_Gripper', Grasp_Cmd_State("close"),
                        transitions={'Success': 'step_' + str(NUM_FOLDING_STEPS),
                                     'Error': 'Fail'})

    for i in range(NUM_FOLDING_STEPS, 0, -1):
        smach.StateMachine.add('step_' + str(i), Joint_Pose_State("folding/step_" + str(i)),
                        transitions={'Success': 'step_' + str(i-1),
                                     'Error': 'Fail'})

    smach.StateMachine.add('step_0', Joint_Pose_State("folding/step_0"),
                        transitions={'Success': 'Success',
                                     'Error': 'Fail'})


# ================================================================ #
Catch_SM = smach.StateMachine(outcomes=["Catch_Success", "Catch_Fail"])

with Catch_SM:
    smach.StateMachine.add('Pre_Catch', Joint_Pose_State("catch"),
                        transitions={'Success': 'Ready_Catch',
                                     'Error': 'Catch_Fail'})

    smach.StateMachine.add('Ready_Catch', Grasp_Cmd_State("open"),
                        transitions={'Success': 'Jetson_Sync_Pass',
                                     'Error': 'Catch_Fail'})

    smach.StateMachine.add('Jetson_Sync_Pass', Jetson_Sync("pass", timeout=30),
                        transitions={'Ready': 'Catch',
                                     'Timeout': 'Catch_Fail'})

    smach.StateMachine.add('Catch', Catch(),
                        transitions={'Success': 'Catch_Success',
                                     'Fail': 'Catch_Fail'})

# ================================================================ #

Reload_SM = smach.StateMachine(outcomes=["Success", "Out_Of_Balls", "Fail"])

with Reload_SM:
    # Assumes already folded

    smach.StateMachine.add('Ball_Status', Ball_Status(),
                        transitions={'2': 'Pickup_1',
                                     '1': 'Pickup_2',
                                     '0': 'Out_Of_Balls'})    

    # Should try to pick it up again
    smach.StateMachine.add('Pickup_1', Pickup_1(),
                        transitions={'Success': 'Unfold',
                                     'Error': 'Unfold'})

    smach.StateMachine.add('Pickup_2', Pickup_2(),
                        transitions={'Success': 'Unfold',
                                     'Error': 'Unfold'})

    smach.StateMachine.add('Unfold', Unfold_SM,
                        transitions={'Success': 'Success',
                                    'Fail': 'Fail'})


# ================================================================ #


Throw_SM = smach.StateMachine(outcomes=["Pass_Complete", "Throw_Success", "Throw_Fail"])

with Throw_SM:

    smach.StateMachine.add('Pre_Throw', Joint_Pose_State("pre_throw"),
                        transitions={'Success': 'Jetson_Sync_Pass',
                                    'Error': 'Throw_Fail'})

    
    # Attempt to catch if this sync times out
    smach.StateMachine.add('Jetson_Sync_Pass', Jetson_Sync("pass"),
                        transitions={'Ready': 'Throw',
                                    'Timeout': 'Throw_Fail'})
    
    
    smach.StateMachine.add('Throw', Async_Joint_Pose_State("throw"),
                        transitions={'Success': 'Wait_to_Release',
                                    'Error': 'Throw_Fail'})

    smach.StateMachine.add('Wait_to_Release', Wait_State(0.2),
                        transitions={'Complete': 'Release'})

    smach.StateMachine.add('Release', Grasp_Cmd_State("open"),
                        transitions={'Success': 'Check_Catch',
                                    'Error': 'Throw_Fail'})
    
    smach.StateMachine.add('Check_Catch', Check_Catch(),
                        transitions={'Caught': 'Pass_Complete',
                                      'Missed': 'Throw_Success',
                                      'Timeout': 'Throw_Fail',
                                      'Not_Catching': 'Throw_Fail'})
    



# ---------------------------------------------------------------- #
#                         Peripherals                              #
# ---------------------------------------------------------------- #

class PCS_State(smach.State):
    def __init__(self, pcs_node_name=None, pcs_node_state=None, pcs_node_cmd=None, state_comm=None):
        smach.State.__init__(self, outcomes=['Success', 'Error'])

        self.read_state_comm = state_comm
        self.pcs_node_state = pcs_node_state
        self.pcs_node_cmd = pcs_node_cmd

        self.pcs_nodes = rospy.get_param("/pcs_nodes")
        self.node_id = self.pcs_nodes.index(pcs_node_name)

class PCS_Activate_State(PCS_State):
    def execute(self, userdata):
        self.pcs_node_cmd(self.node_id, PCScmd.ACTIVATE)

        while self.pcs_node_state(self.node_id) == PCSstate.NA or self.pcs_node_state(self.node_id) == PCSstate.DISABLED:
            rospy.sleep(0.5)
        
        if self.pcs_node_state(self.node_id) == PCSstate.GOOD:
            return 'Success'
        else:
            return 'Error'

class PCS_Deactivate_State(PCS_State):
    def execute(self, userdata):
        self.pcs_node_cmd(self.node_id, PCScmd.DEACTIVATE)

        while self.pcs_node_state(self.node_id) != PCSstate.DISABLED:
            rospy.loginfo("Deactivating node: " + str(self.pcs_nodes[self.node_id]) + " Node State: " + str(self.pcs_node_state(self.node_id)))
            rospy.sleep(0.5)

        return 'Success'


class PCS_Shutdown_State(PCS_State):
    def execute(self, userdata):
        self.pcs_node_cmd(self.node_id, PCScmd.SHUTDOWN)

        while self.pcs_node_state(self.node_id) != PCSstate.SHUTDOWN:
            rospy.sleep(0.5)

        return 'Success'





class Teensy_Comm_Check(PCS_Activate_State):
    pass

class Wait_for_TE(PCS_Activate_State):
    pass

class Activate_Longeron_Cams(PCS_Activate_State):
    pass

class Deactivate_Longeron_Cams(PCS_Deactivate_State):
    pass

class Activate_Depth_Cam(PCS_Activate_State):
    pass

class Deactivate_Depth_Cam(PCS_Deactivate_State):
    pass

class Shutdown_Depth_Cam(PCS_Shutdown_State):
    pass
