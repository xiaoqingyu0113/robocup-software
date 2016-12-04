#include "SingleRobotPathPlanner.hpp"
#include "TargetVelPathPlanner.hpp"
#include "DirectTargetPathPlanner.hpp"
#include "TargetVelPathPlanner.hpp"
#include "EscapeObstaclesPathPlanner.hpp"
#include "RRTPlanner.hpp"
#include "PivotPathPlanner.hpp"
#include "LineKickPlanner.hpp"

namespace Planning {

REGISTER_CONFIGURABLE(SingleRobotPathPlanner);

ConfigDouble* SingleRobotPathPlanner::_goalChangeThreshold;
ConfigDouble* SingleRobotPathPlanner::_replanTimeout;

void SingleRobotPathPlanner::createConfiguration(Configuration* cfg) {
    _replanTimeout = new ConfigDouble(cfg, "PathPlanner/replanTimeout", 5);
    _goalChangeThreshold =
        new ConfigDouble(cfg, "PathPlanner/goalChangeThreshold", 0.025);
}

std::unique_ptr<SingleRobotPathPlanner> PlannerForCommandType(
    MotionCommand::CommandType type) {
    SingleRobotPathPlanner* planner = nullptr;
    switch (type) {
        case MotionCommand::PathTarget:
            planner = new RRTPlanner(250);
            break;
        case MotionCommand::DirectPathTarget:
            planner = new DirectTargetPathPlanner();
            break;

        case MotionCommand::Pivot:
            planner = new PivotPathPlanner();
            break;
        case MotionCommand::WorldVel:
            planner = new TargetVelPathPlanner();
            break;
        case MotionCommand::LineKick:
            planner = new LineKickPlanner();
            break;
        case MotionCommand::None:
            planner = new EscapeObstaclesPathPlanner();
            break;
        default:
            debugThrow("Command not implemented");
            planner = new EscapeObstaclesPathPlanner();
            break;
    }

    return std::unique_ptr<SingleRobotPathPlanner>(planner);
}

void SingleRobotPathPlanner::allDynamicToStatic(
    Geometry2d::ShapeSet& obstacles,
    const std::vector<DynamicObstacle>& dynamicObstacles) {
    for (auto& dynObs : dynamicObstacles) {
        obstacles.add(dynObs.getStaticObstacle());
    }
}

void SingleRobotPathPlanner::splitDynamic(
    Geometry2d::ShapeSet& obstacles, std::vector<DynamicObstacle>& dynamicOut,
    const std::vector<DynamicObstacle>& dynamicObstacles) {
    for (auto& dynObs : dynamicObstacles) {
        if (dynObs.hasPath()) {
            dynamicOut.push_back(dynObs);
        } else {
            obstacles.add(dynObs.getStaticObstacle());
        }
    }
}

boost::optional<std::function<AngleInstant(MotionInstant)>>
angleFunctionForCommandType(const Planning::RotationCommand& command) {
    switch (command.getCommandType()) {
        case RotationCommand::FacePoint: {
            Geometry2d::Point targetPt =
                static_cast<const Planning::FacePointCommand&>(command)
                    .targetPos;
            std::function<AngleInstant(MotionInstant)> function =
                [targetPt](MotionInstant instant) {
                    return AngleInstant(instant.pos.angleTo(targetPt));
                };
            return function;
        }
        case RotationCommand::FaceAngle: {
            float angle = static_cast<const Planning::FaceAngleCommand&>(
                              command).targetAngle;
            std::function<AngleInstant(MotionInstant)> function =
                [angle](MotionInstant instant) { return AngleInstant(angle); };
            return function;
        }
        case RotationCommand::None:
            return boost::none;
        default:
            debugThrow("RotationCommand Not implemented");
            return boost::none;
    }
}

bool SingleRobotPathPlanner::shouldReplan(
    const SinglePlanRequest& planRequest) {
    const auto currentInstant = planRequest.startInstant;
    const MotionConstraints& motionConstraints =
        planRequest.robotConstraints.mot;
    const Geometry2d::ShapeSet& obstacles = planRequest.obstacles;
    const Path* prevPath = planRequest.prevPath.get();

    if (!prevPath) return true;

    // if this number of microseconds passes since our last path plan, we
    // automatically replan
    const RJ::Seconds kPathExpirationInterval = RJ::Seconds(replanTimeout());
    if ((RJ::now() - prevPath->startTime()) > kPathExpirationInterval) {
        return true;
    }

    // Evaluate where the path says the robot should be right now
    RJ::Seconds timeIntoPath =
        (RJ::now() - prevPath->startTime()) + RJ::Seconds(1) / 60;

    boost::optional<RobotInstant> optTarget = prevPath->evaluate(timeIntoPath);
    // If we went off the end of the path, use the end for calculations.
    MotionInstant target =
        optTarget ? optTarget->motion : prevPath->end().motion;

    // invalidate path if current position is more than the replanThreshold away
    // from where it's supposed to be right now
    float pathError = (target.pos - currentInstant.pos).mag();
    float replanThreshold = *motionConstraints._replan_threshold;
    if (*motionConstraints._replan_threshold != 0 &&
        pathError > replanThreshold) {
        return true;
    }

    // Replan if we enter new obstacles
    RJ::Seconds hitTime;
    if (prevPath->hit(obstacles, timeIntoPath, &hitTime)) {
        return true;
    }

    return false;
}
}  // namespace Planning
