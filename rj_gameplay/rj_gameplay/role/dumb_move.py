import stp

import rj_gameplay.eval
import rj_gameplay.skill as skills
from rj_gameplay.skill import move
import stp.skill as skill
import numpy as np

from rj_msgs.msg import RobotIntent


class DumbMove(stp.role.Role):
    def __init__(self, robot: stp.rc.Robot, target_point, face_point) -> None:
        super().__init__(robot)

        self.target_point = target_point
        self.face_point = face_point

        self.move_skill = None

    def tick(
        self, world_state: stp.rc.WorldState, target_point=None, face_point=None
    ) -> RobotIntent:
        if target_point is not None:
            self.target_point = target_point
            # TODO: clean this up
            self.move_skill = move.Move(
                robot=self.robot,
                target_point=self.target_point,
                face_point=self.face_point,
            )

        if face_point is not None:
            self.face_point = face_point
            self.move_skill = move.Move(
                robot=self.robot,
                target_point=self.target_point,
                face_point=self.face_point,
            )

        # create skill with correct target & face_point
        if self.move_skill is None:
            self.move_skill = move.Move(
                robot=self.robot,
                target_point=self.target_point,
                face_point=self.face_point,
            )

        intent = self.move_skill.tick(world_state)
        return intent

    def is_done(self, world_state) -> bool:
        return self.move_skill.is_done(world_state)
