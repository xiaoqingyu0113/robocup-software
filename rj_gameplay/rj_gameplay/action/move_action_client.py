# TODO: add cancel move option

import rclpy
from rclpy.action import ActionClient
from rclpy.node import Node

from rj_msgs.action import Move

from rj_msgs.msg import ServerIntent, RobotIntent, PathTargetMotionCommand


class MoveActionClient(Node):
    def __init__(self, robot_id):
        super().__init__("move_action_client_{:02d}".format(robot_id))
        self._robot_id = robot_id
        self._action_client = ActionClient(self, Move, "move")
        self._curr_goal = Move.Goal()
        self._goal_handle = None
        self.curr_feedback = Move.Feedback()

    def send_goal(self, server_intent: ServerIntent):
        if len(server_intent.intent.motion_command.path_target_command) > 0:
            new_target_position = (
                server_intent.intent.motion_command.path_target_command[
                    0
                ].target.position
            )
            if self._curr_goal is not None:
                path_target_command = (
                    self._curr_goal.server_intent.intent.motion_command.path_target_command
                )
                if (
                    len(path_target_command) > 0
                    and path_target_command[0].target.position == new_target_position
                ):
                    self.cancel_goal()
        goal_msg = Move.Goal()
        goal_msg.server_intent = server_intent

        self._action_client.wait_for_server()

        self._send_goal_future = self._action_client.send_goal_async(
            goal_msg, feedback_callback=self.feedback_callback
        )

        self._send_goal_future.add_done_callback(self.goal_response_callback)

    def goal_response_callback(self, future):
        goal_handle = future.result()
        if not goal_handle.accepted:
            self.get_logger().info("Goal not accepted by server.")
            return

        self._goal_handle = goal_handle
        self.get_logger().info("Goal accepted by server!")

        self._get_result_future = goal_handle.get_result_async()
        self._get_result_future.add_done_callback(self.get_result_callback)

    def get_result_callback(self, future):
        result = future.result().result
        self.get_logger().info("Result:", result)
        # rclpy.shutdown()

    def feedback_callback(self, feedback_msg):
        feedback = feedback_msg.feedback
        self.get_logger().info("Got feedback:", feedback)

    def cancel_done(self, future):
        cancel_response = future.result()
        if len(cancel_response.goals_canceling) > 0:
            self.get_logger().info("Goal successfully canceled")
            return cancel_response
        else:
            self.get_logger().info("Goal failed to cancel")
            return cancel_response

    def cancel_goal(self):
        if self._goal_handle is None:
            return
        self.get_logger().info("Canceling goal")
        # Cancel the goal
        future = self._goal_handle.cancel_goal_async()
        future.add_done_callback(self.cancel_done)
