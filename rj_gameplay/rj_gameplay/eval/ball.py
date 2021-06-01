import sys
sys.path.insert(1, "../../stp")
import rc
import math
import numpy as np
from typing import Optional
sys.path.append("/utils")
import constants

class Ball:
    
    def distance(loc1, loc2):
        return sqrt(abs(loc1[1] - loc2[1])**2 + abs(loc1[0] - loc2[0])**2)
        #return 0.0
    """manifestation of a ball"""

    '''
    def is_moving_towards_our_goal() -> bool:
    # see if the ball is moving much
    if main.ball().vel.mag() > 0.18:  # Tuned based on vision noise
        # see if it's moving somewhat towards our goal
        if main.ball().vel.dot(robocup.Point(0, -1)) > 0:
            ball_path = robocup.Line(main.ball().pos, (
                main.ball().pos + main.ball().vel.normalized()))

            fudge_factor = 0.15  # TODO: this could be tuned better
            WiderGoalSegment = robocup.Segment(
                robocup.Point(constants.Field.GoalWidth / 2.0 + fudge_factor,
                              0),
                robocup.Point(-constants.Field.GoalWidth / 2.0 - fudge_factor,
                              0))

            pt = ball_path.segment_intersection(WiderGoalSegment)
            return pt != None

    return False
    '''

    def intersect(s1, s2, b1, b2):
    	''' do the lines s and b intersect?'''
        print(s1[0], s1[1])
        print(s2[0], s2[1])
        print(b1[0], b1[1])
        print(b2[0], b2[1])
        
        #x check
        xmin = min(s1[0], s2[0])
        xmax = max(s1[0], s2[0])
        x = ((xmin <= b1[0] <= xmax) or (xmin <= b2[0] <= xmax))
        #y check
        ymin = min(s1[1], s2[1])
        ymax = max(s1[1], s2[1])
        y = ((ymin <= b1[1] <= ymax) or (ymin <= b2[1] <= ymax))
        return (x and y)

    def is_moving_backward(ball, field):

        '''
        Is the ball moving towards the opponent's goal (forward)
        or towards our goal (backward)?
        '''
        
        vel = np.asarray(ball.vel)
        mag = math.sqrt(vel[0]**2 + vel[1]**2)
        nvel = vel / mag
        if mag > 0.18: #vision noise should be thresholded out
            if vel.dot([0, -1]) > 0:	
                ball_path = [ball.pos[:-1], (
                ball.pos[:-1] + nvel)]
                print(ball_path[0], ball_path[1])
                fudge_factor = 0.15  # TODO: this could be tuned better
                GoalSegment = [[field.goal_width_m / 2.0 + fudge_factor,
                            0],
                    [-field. goal_width_m/2.0 - fudge_factor,
                            0]]   
                #print(GoalSegment[0], GoalSegment[1])
                #pt = ball_path.segment_intersection(WiderGoalSegment)
                pt = intersect(GoalSegment[0], GoalSegment[1], ball_path[0], ball_path[1])
                return pt
        return False

    def is_in_our_goalie_zone(ball, field):
        if ball != None:
            return False
            width = field.penalty_long_dist_m / 2
            height = field.penalty_short_dist_m
            
            if ball.pos[1] >= height: 
                return False
            elif abs(ball.pos[0]) >= width:
                return False
            return True #if both checks pass
            
        else:
            return False

    def we_are_closer(worldstate):
       
        ball = rc.ball()
        our_robots = rc.our_robots()
        their_robots = rc.their_robots()
        return min([distance(ball.pos[:-1], rob.pos[:-1]) for rob in their_robots]) > min([distance(ball.pos[:-1], rob.pos[:-1]) for rob in our_robots])
        
        '''
        return min([(ball.pos - rob.pos).mag()
                for rob in main.system_state().their_robots]) > min(
                    [(main.ball().pos - rob.pos).mag()
                     for rob in main.system_state().our_robots])
        '''
        
    	return False

    def opponent_is_much_closer(worldstate):
        ball = rc.ball()
        our_robots = rc.our_robots()
        their_robots = rc.their_robots()
        return min([distance(ball.pos[:-1], rob.pos[:-1]) for rob in their_robots]) * 3 < min([distance(ball.pos[:-1], rob.pos[:-1]) for rob in our_robots])

    def moving_slow(ball):
        vel = sqrt(ball.vel()[0]**2 + ball.vel()[1]**2)
        return vel <= constants.Evaluation.SlowThreshold

    FrictionCoefficient = 0.04148
    GravitationalCoefficient = 9.81  # in m/s^2
    decel = GravitationalCoefficient * FrictionCoefficient

    def predict_stop_time(ball):
        vel = ball.vel()
        v = sqrt(vel[0]**2 + vel[1]**2)
        return v / decel

    def predict_stop(ball):
        #return ball.predict_pos(ball.predict_seconds_to_stop())
        vel = ball.vel()
        v = sqrt(vel[0]**2 + vel[1]**2)
    	return (v / 2) * predict_stop_time(ball) #very simplified

    def rev_predict(dist, ball):
        """predict how much time it will take the ball to travel the given distance"""
        #return main.ball().estimate_seconds_to_dist(dist)
        vel = ball.vel()
        vi_sq = vel[0]**2 + vel[1]**2
        if dist > predict_stop(ball):
            return -1 #it will not reach this point
        #vf^2 - vi^2 = 2ad => vf = sqrt(vi^2 + 2ad)
        change = 2 * decel * dist
        vf_sq = vi_sq - change
        return sqrt(vf_sq)

    def opponent_with_ball(ball, their_robots, our_robots):
        c_dist = float('inf')
        c_bot = None
        for bot in their_robots:
            if bot.visible:
                dist = distance(ball.pos, bot.pos)
                if dist < c_dist:
                    c_bot = bot
                    c_dist = dist
        for bot in our_robots:
            if bot.visible:
                dist = distance(ball.pos, bot.pos)
                if dist < c_dist:
                    return None
        return c_bot

    def our_robot_with_ball(ball, their_robots, our_robots):
        c_dist = float('inf')
        c_bot = None
        for bot in our_robots:
            if bot.visible:
                dist = distance(ball.pos, bot.pos)
                if dist < c_dist:
                    c_bot = bot
                    c_dist = dist
        for bot in their_robots:
            if bot.visible:
                dist = distance(ball.pos, bot.pos)
                if dist < c_dist:
                    return None
        return c_bot

    def robot_has_ball(ball, robot):
        mouth_half_angle = math.pi / 12
        mouth_max_dist = 1.13 * (constants.Robot.Radius + constants.Ball.Radius)
        # Create triangle between bot pos and two points of the mouth
        A = robot.pos[:-1]
        B = A + [mouth_max_dist * math.cos(robot.pos[-1] - mouth_half_angle), mouth_max_dist * math.sin(robot.pos[-1] - mouth_half_angle)]
        C = A + [mouth_max_dist * math.cos(robot.pos[-1] + mouth_half_angle), mouth_max_dist * math.sin(robot.pos[-1] + mouth_half_angle)]
        D = ball.pos
        
        # Barycentric coordinates to solve whether the ball is in that triangle
        area = 0.5 * (-B[1] * C[0] + A[1] * (-B[0] + C[0]) + A[0] *
                  (B[1] - C[1]) + B[0] * C[1])
        s = 1 / (2 * area) * (A[1] * C[0] - A[0] * C[1] + (C[1] - A[1]) * D[0] +
                          (A[0] - C[0]) * D[1])
        t = 1 / (2 * area) * (A[0] * B[1] - A[1] * B[0] + (A[1] - B[1]) * D[0] +
                          (B[0] - A[0]) * D[1])
        
        # Due to the new camera configuration in the 2019 year,
        # the ball dissapears consistently when we go to capture a ball near the
        # edge of the field. This causes the ball to "appear" inside the robot
        # so we should assume that if the ball is inside, we probably have
        # the ball
        ball_inside_robot = distance(robot.pos[:-1], ball.pos) < \
                            constants.Robot.Radius + constants.Ball.Radius

        return (s > 0 and t > 0 and (1 - s - t) > 0) or ball_inside_robot

    def time_to_ball(ball, robot):
        
        '''
        max_vel = robocup.MotionConstraints().max_speed
    max_accel = robocup.MotionConstraints().max_accel
    delay = .1  # TODO: tune this better
    rpos = robot.pos
    bpos = main.ball().pos
    # calculate time for self to reach ball using max_vel + a slight delay for capture
    dist_to_ball = robot.pos.dist_to(main.ball().pos)
    return (dist_to_ball / max_vel) + delay
        '''
        max_vel = 2.0
        max_accel = 0.5
        delay = 0.1
        rpos = robot.pos[:-1]
        bpos = ball.pos
        # calculate time for self to reach ball using max_vel + a slight delay for capture
        dist = distance(rpos, bpos)
    	return (dist / max_vel) + delay

    #testing purposes
    ball = rc.Ball([0,4.5],[0, -1], True)
    field = rc.Field(9, 6, 1, 1, 2, 0.5, 0.5, 1, 2, 1.5, 3, 1, 8, 10)

    forward = is_moving_backward(ball, field)
    if forward:
    	print("Ball is moving towards our goal.")
    else:
    	print("Ball is not moving towards our goal.")
	
'''
import main
import robocup
import constants
import math
from typing import Optional


def is_moving_towards_our_goal() -> bool:
    # see if the ball is moving much
    if main.ball().vel.mag() > 0.18:  # Tuned based on vision noise
        # see if it's moving somewhat towards our goal
        if main.ball().vel.dot(robocup.Point(0, -1)) > 0:
            ball_path = robocup.Line(main.ball().pos, (
                main.ball().pos + main.ball().vel.normalized()))

            fudge_factor = 0.15  # TODO: this could be tuned better
            WiderGoalSegment = robocup.Segment(
                robocup.Point(constants.Field.GoalWidth / 2.0 + fudge_factor,
                              0),
                robocup.Point(-constants.Field.GoalWidth / 2.0 - fudge_factor,
                              0))

            pt = ball_path.segment_intersection(WiderGoalSegment)
            return pt != None

    return False


def is_in_our_goalie_zone() -> bool:
    if main.ball() != None:
        return constants.Field.OurGoalZoneShape.contains_point(main.ball().pos)
    else:
        return False


# TODO use for situation analysis
def we_are_closer() -> bool:
    return min([(main.ball().pos - rob.pos).mag()
                for rob in main.system_state().their_robots]) > min(
                    [(main.ball().pos - rob.pos).mag()
                     for rob in main.system_state().our_robots])


# TODO use for situation analysis
def opponent_is_much_closer() -> bool:
    return min([(main.ball().pos - rob.pos).mag()
                for rob in main.system_state().their_robots]) * 3 < min(
                    [(main.ball().pos - rob.pos).mag()
                     for rob in main.system_state().our_robots])


def moving_slow() -> bool:
    return main.ball().vel.mag() <= constants.Evaluation.SlowThreshold


FrictionCoefficient = 0.04148
GravitationalCoefficient = 9.81  # in m/s^2


def predict_stop_time() -> float:
    return main.ball().predict_seconds_to_stop()


def predict_stop() -> float:
    return main.ball().predict_pos(main.ball().predict_seconds_to_stop())


def rev_predict(dist) -> float:
    """predict how much time it will take the ball to travel the given distance"""
    return main.ball().estimate_seconds_to_dist(dist)


# returns a Robot or None indicating which opponent has the ball
def opponent_with_ball() -> Optional[robocup.OpponentRobot]:
    closest_bot, closest_dist = None, float("inf")
    for bot in main.their_robots():
        if bot.visible:
            dist = (bot.pos - main.ball().pos).mag()
            if dist < closest_dist:
                closest_bot, closest_dist = bot, dist

    if closest_bot is None:
        return None
    else:
        if robot_has_ball(closest_bot):
            return closest_bot
        else:
            return None


## If our robot has the ball, then returns that robot. Otherwise None
#
# @return Robot: a robot or None
def our_robot_with_ball() -> Optional[robocup.OurRobot]:
    closest_bot, closest_dist = None, float("inf")
    for bot in main.our_robots():
        if bot.visible:
            dist = (bot.pos - main.ball().pos).mag()
            if dist < closest_dist:
                closest_bot, closest_dist = bot, dist

    if closest_bot == None:
        return None
    else:
        if robot_has_ball(closest_bot):
            return closest_bot
        else:
            return None


# based on face angle and distance, determines if the robot has the ball
def robot_has_ball(robot: robocup.Robot) -> bool:
    mouth_half_angle = 15 * math.pi / 180  # Angle from front
    max_dist_from_mouth = 1.13 * (
        constants.Robot.Radius + constants.Ball.Radius)

    # Create triangle between bot pos and two points of the mouth
    A = robot.pos
    B = A + robocup.Point(
        max_dist_from_mouth * math.cos(robot.angle - mouth_half_angle),
        max_dist_from_mouth * math.sin(robot.angle - mouth_half_angle))
    C = A + robocup.Point(
        max_dist_from_mouth * math.cos(robot.angle + mouth_half_angle),
        max_dist_from_mouth * math.sin(robot.angle + mouth_half_angle))
    D = main.ball().pos

    # Barycentric coordinates to solve whether the ball is in that triangle
    area = 0.5 * (-B.y * C.x + A.y * (-B.x + C.x) + A.x *
                  (B.y - C.y) + B.x * C.y)
    s = 1 / (2 * area) * (A.y * C.x - A.x * C.y + (C.y - A.y) * D.x +
                          (A.x - C.x) * D.y)
    t = 1 / (2 * area) * (A.x * B.y - A.y * B.x + (A.y - B.y) * D.x +
                          (B.x - A.x) * D.y)

    # Due to the new camera configuration in the 2019 year,
    # the ball disappears consistently when we go to capture a ball near the
    # edge of the field. This causes the ball to "appear" inside the robot
    # so we should assume that if the ball is inside, we probably have
    # the ball
    ball_inside_robot = (robot.pos - main.ball().pos).mag() < \
                        constants.Robot.Radius + constants.Ball.Radius

    return (s > 0 and t > 0 and (1 - s - t) > 0) or ball_inside_robot


def time_to_ball(robot: robocup.Robot) -> float:
    max_vel = robocup.MotionConstraints.MaxRobotSpeed.value
    max_accel = robocup.MotionConstraints.MaxRobotAccel.value
    delay = .1  # TODO: tune this better
    rpos = robot.pos
    bpos = main.ball().pos
    # calculate time for self to reach ball using max_vel + a slight delay for capture
    dist_to_ball = robot.pos.dist_to(main.ball().pos)
    return (dist_to_ball / max_vel) + delay
'''
