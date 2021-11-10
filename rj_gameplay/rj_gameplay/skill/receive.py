from abc import ABC, abstractmethod

import rj_gameplay.eval as eval
import argparse
import py_trees
import sys
import time
import numpy as np
from typing import Optional

import stp.skill as skill
import stp.role as role
from rj_gameplay.skill import settle, capture
from rj_msgs.msg import RobotIntent, SettleMotionCommand
import stp.rc as rc
from rj_msgs import msg



"""
A skill version of receive so that actions don't have to be called in tactics
"""

class Receive(skill.ISkill):
    def __init__(self, robot: rc.Robot = None):
        self.robot = robot

        self.__name__ = 'receive skill'
        self.settle = settle.Settle(robot)
        self.capture = capture.Capture(robot)

    def tick(self, robot: rc.Robot, world_state: rc.WorldState,
             intent: RobotIntent):
        if self.settle.is_done(world_state):
            return self.capture.tick(robot, world_state, intent)
        else:
            return self.settle.tick(robot, world_state, intent)


    def is_done(self, world_state:rc.WorldState) -> bool:

        return self.capture.is_done(world_state)


    def __str__(self):
        return f"Receive[Settle(robot={self.settle.robot.id if self.settle.robot is not None else '??'}), Capture(robot={self.capture.robot.id if self.capture.robot is not None else '??'})]"