from dataclasses import dataclass
from typing import List, Optional
from typing import Dict, Generic, List, Optional, Tuple, Type, TypeVar

import stp.rc as rc
import stp.tactic as tactic
import stp.role as role

import rj_gameplay.eval
import rj_gameplay.skill as skills
from rj_gameplay.skill import pivot_kick, receive
import stp.skill as skill
import numpy as np
from math import atan2

import stp.global_parameters as global_parameters


class PassToClosestReceiver(role.CostFn):
    """
    A cost function for how to choose a robot to pass to
    """
    def __init__(self,
                 target_point: Optional[np.ndarray] = None,
                 passer_robot: rc.Robot = None):
        self.target_point = target_point
        self.passer_robot = passer_robot
        self.chosen_receiver = None

    def __call__(
        self,
        robot: rc.Robot,
        prev_result: Optional["RoleResult"],
        world_state: rc.WorldState,
    ) -> float:

        if robot is None or self.target_point is None:
            return 99
        # TODO (#1669)
        if not robot.visible:
            return 99
        if self.passer_robot is not None and robot.id == self.passer_robot.id:
            # can't pass to yourself
            return 99
        if self.chosen_receiver is not None and self.chosen_receiver.id == robot.id:
            return -99

        # always pick closest receiver
        raw_dist = np.linalg.norm(robot.pose[0:2] - self.target_point)
        return raw_dist / global_parameters.soccer.robot.max_speed

    def unassigned_cost_fn(
        self,
        prev_result: Optional["RoleResult"],
        world_state: rc.WorldState,
    ) -> float:

        #TODO: Implement real unassigned cost function
        return role.BIG_STUPID_NUMBER_CONST_FOR_UNASSIGNED_COST_PLS_CHANGE


class PasserCost(role.CostFn):
    """
    A cost function for how to choose a robot that will pass
    TODO: Implement a better cost function
    """

    def __call__(self,
                robot:rc.Robot,
                prev_result:Optional["RoleResult"],
                world_state:rc.WorldState) -> float:
        if robot.has_ball_sense:
            return 0
        else:
            # closest to ball
            return np.linalg.norm(world_state.ball.pos - robot.pose[0:2])

    def unassigned_cost_fn(
        self,
        prev_result: Optional["RoleResult"],
        world_state: rc.WorldState,
    ) -> float:

        #TODO: Implement real unassigned cost function
        return role.BIG_STUPID_NUMBER_CONST_FOR_UNASSIGNED_COST_PLS_CHANGE


class PassToOpenReceiver(role.CostFn):
    """
    A cost function for how to choose a robot to pass to
    TODO: Implement a better cost function
    CURRENTLY NOT READY FOR USE
    """
    def __init__(self,
                 target_point: Optional[np.ndarray] = None,
                 passer_robot: rc.Robot = None):
        self.target_point = target_point
        self.passer_robot = passer_robot
        self.chosen_receiver = None

    def __call__(
        self,
        robot: rc.Robot,
        prev_result: Optional["RoleResult"],
        world_state: rc.WorldState,
    ) -> float:

        if robot is None or self.target_point is None:
            return 1e9
        # TODO (#1669)
        if not robot.visible:
            return 1e9
        if self.passer_robot is not None and robot.id == self.passer_robot.id:
            # can't pass to yourself
            return 1e9
        # if self.chosen_receiver is not None and self.chosen_receiver.id == robot.id:
        #     return -1e9

        # TODO: pick "most open" pass
        if self.passer_robot is not None and robot.id != self.passer_robot.id:
            pass_dist = np.linalg.norm(passer_robot.pose[0:2] -
                                       robot.pose[0:2])
            goal_to_receiver = np.linalg.norm(robot.pose[0:2] -
                                              rc.Field.their_goal_loc)
            cost = 0
            for enemy in world_state.their_robots:
                cost -= 10 * np.linalg.norm(enemy.pose[0:2] - robot.pose[0:2])
        else:
            return 1e9

    def unassigned_cost_fn(
        self,
        prev_result: Optional["RoleResult"],
        world_state: rc.WorldState,
    ) -> float:

        #TODO: Implement real unassigned cost function
        return role.BIG_STUPID_NUMBER_CONST_FOR_UNASSIGNED_COST_PLS_CHANGE


class PassToBestReceiver(role.CostFn):
    """
    A cost function for how to choose a robot to pass to

    """
    def __init__(self, passer_robot: rc.Robot = None):
        self.passer_robot = passer_robot
        # self.chosen_receiver = None

    def __call__(self, robot: rc.Robot, prev_result: Optional["RoleResult"],
                 world_state: rc.WorldState) -> float:
        if world_state is not None:
            min_dist = 999
            for our_robot in world_state.our_robots:
                dist = np.linalg.norm(world_state.ball.pos -
                                      our_robot.pose[0:2])
                if min_dist > dist:
                    min_dist = dist
                    self.passer_robot = our_robot
        if robot is None:
            return 1e9
        # if not robot.visible:
        #     return 1e9
        if self.passer_robot is not None and robot.id == self.passer_robot.id:
            # can't pass to yourself
            return 1e9
        angle_threshold = 5
        dist_threshold = 1.5
        backpass_punish_weight = 0.5
        if robot.id != self.passer_robot.id:
            pass_dist = np.linalg.norm(self.passer_robot.pose[0:2] -
                                       robot.pose[0:2])

            cost = 0
            goal_to_receiver = np.linalg.norm(robot.pose[0:2] -
                                              world_state.field.their_goal_loc)
            goal_to_passer = np.linalg.norm(self.passer_robot.pose[0:2] -
                                            world_state.field.their_goal_loc)
            cost += (goal_to_receiver -
                     goal_to_passer) * backpass_punish_weight
            for enemy in world_state.their_robots:
                passer_to_enemy = np.linalg.norm(enemy.pose[0:2] -
                                                 self.passer_robot.pose[0:2])
                if passer_to_enemy <= pass_dist:
                    vec_to_passer = robot.pose[0:2] - self.passer_robot.pose[
                        0:2]
                    vec_to_enemy = enemy.pose[0:2] - self.passer_robot.pose[0:2]
                    angle = np.degrees(
                        abs(
                            atan2(np.linalg.det([vec_to_passer, vec_to_enemy]),
                                  np.dot(vec_to_passer, vec_to_enemy))))
                    if angle < angle_threshold:
                        return 1e9
                enemy_to_receiver = np.linalg.norm(robot.pose[0:2] -
                                                   enemy.pose[0:2])
                if enemy_to_receiver < dist_threshold:
                    cost += (dist_threshold - enemy_to_receiver)**2
            return cost
        else:
            return 0

    def unassigned_cost_fn(
        self,
        prev_result: Optional["RoleResult"],
        world_state: rc.WorldState,
    ) -> float:

        #TODO: Implement real unassigned cost function
        return role.BIG_STUPID_NUMBER_CONST_FOR_UNASSIGNED_COST_PLS_CHANGE


class Pass(tactic.ITactic):
    """
    A passing tactic which captures then passes the ball
    """

    def __init__(self):
        self.pivot_kick = tactic.SkillEntry(
            pivot_kick.PivotKick(robot=None,
                                 target_point=np.array([0., 0.]),
                                 chip=False,
                                 kick_speed=4.0))
        self.receive = tactic.SkillEntry(receive.Receive())
        self.receiver_cost = PassToBestReceiver()
        self.passer_cost = PasserCost()

    def compute_props(self):
        pass

    def create_request(self, **kwargs) -> role.RoleRequest:
        """Creates a sane default RoleRequest.
        :return: A list of size 1 of a sane default RoleRequest.
        """
        pass

    def find_potential_receiver(self, world_state: rc.WorldState) -> rc.Robot:
        cost = 1e9
        receiver = None
        for robot in world_state.our_robots:
            curr_cost = self.receiver_cost(robot, None, world_state)
            if curr_cost < cost:
                cost = curr_cost
                receiver = robot
        # print(receiver.id)
        return receiver

    def find_passer(self, world_state: rc.WorldState) -> rc.Robot:
        cost = 1e9
        passer = None
        for robot in world_state.our_robots:
            curr_cost = self.passer_cost(robot, None, world_state)
            if curr_cost < cost:
                cost = curr_cost
                passer = robot
        return passer

    def get_requests(
        self, world_state:rc.WorldState, props) -> List[tactic.RoleRequests]:
        """ Checks if we have the ball and returns the proper request
        :return: A list of size 2 of role requests
        """

        role_requests: tactic.RoleRequests = {}

        if self.pivot_kick.skill.is_done(world_state):
            receive_request = role.RoleRequest(role.Priority.MEDIUM, True,
                                               self.receiver_cost)
            role_requests[self.receive] = [receive_request]
        else:
            passer_request = role.RoleRequest(role.Priority.HIGH, True,
                                              self.passer_cost)
            role_requests[self.pivot_kick] = [passer_request]



        return role_requests

    def tick(self, world_state: rc.WorldState,
             role_results: tactic.RoleResults) -> List[tactic.SkillEntry]:
        """
        :return: A list of size 1 or 2 skills depending on which roles are filled and state of aiming
        TODO: Come up with better timings for starting receive
        """
        pivot_result = role_results[self.pivot_kick]
        receive_result = role_results[self.receive]
        if pivot_result and pivot_result[0].is_filled():
            self.receiver_cost.passer_robot = pivot_result[0].role.robot
            # self.pivot_kick.skill.target_point = np.array(receive_result[0].role.robot.pose[0:2])
            self.pivot_kick.skill.target_point = self.find_potential_receiver(world_state).pose[0:2]
            self.pivot_kick.skill.pivot_point = np.array(
                pivot_result[0].role.robot.pose[0:2])

            # self.receiver_cost.potential_receiver = receive_result[
            #     0].role.robot
            # return [self.receive]
            # elif pivot_result and pivot_result[0].is_filled():


            # self.pivot_kick.skill.pivot.target_point =
            # if potential_receiver is not None:
            #     self.pivot_kick.skill.pivot.target_point = np.array(
            #         [potential_receiver.pose[0], potential_receiver.pose[1]])
            return [self.pivot_kick]
        elif receive_result and receive_result[0].is_filled(): 
            return [self.receive]
        return []

    def is_done(self, world_state:rc.WorldState):
        return self.receive.skill.is_done(world_state)
