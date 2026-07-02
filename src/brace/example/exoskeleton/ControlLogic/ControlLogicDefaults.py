import brace.example.exoskeleton.ControlLogic.FSM as FSM
import brace.example.exoskeleton.ControlLogic.ProportionalControlLogic as Proportional
import brace.example.exoskeleton.ControlLogic.Standing as Standing
from brace.Server.Core.ControlLogic import IControlLogic
from brace.example.exoskeleton.ControlLogicLookup import ControlLogicEnum
from typing import Callable

class HardcodedDefaults():
    """
        These are hardcoded defaults for hysteresis. The times are in seconds.
        And thus the force must be maintained for 10 ms for stance/swing changes,
        and velocity must be maintained for 50ms for sub-phase changes.
    """
    forceHysteresisTime = 0.01
    velocityHysteresisTime = 0.050

def createControlLogics(initDefaults: dict) -> dict[ControlLogicEnum, Callable[[int], IControlLogic]]:
    """
        Initializes configuration for the control logic classes that are set up.
        Note that these are lambda functions that take in one parameter for the index in the 
        RobotAssemblyABC. These controllers are initialized all with the same configuration values
        as defined in this factory function.  
        
        Some of these numbers are taken from the .ini file, others are hardcoded.

        :param initDefaults: Dictionary containing the default parameters in the .ini file.
        :type initDefaults: dict
        :return: Dictionary containing the enum as the key, and the Callable function as the value.
        :rtype: dict[ControlLogicEnum, Callable[[int], IControlLogic]]
    """
    fsmControlLogic = lambda index: FSM.FSMControlLogic(forceSensorThresholdInitialContact = initDefaults['walkFSM5IcThresholdSpinBox'], # mV
                                    forceSensorThresholdSwing = initDefaults['walkFSM5ToThresholdSpinBox'], # mV
                                    deadZoneTime = initDefaults['walkFSM5DeadZoneTimeDoubleSpinBox'], #s,
                                    velocityEarlyToMidStanceThreshold = initDefaults['walkFSM5EarlyToMidStanceThresholdSpinBox'],
                                    velocityMidToLateStanceThreshold = initDefaults['walkFSM5MidToLateStanceThresholdSpinBox'],
                                    velocityEarlyToLateSwingThreshold = initDefaults['walkFSM5EarlyToLateSwingThresholdSpinBox'],
                                    stateTorques = { FSM.States.WAITING: 0,
                                                FSM.States.EARLY_STANCE: 0,
                                                FSM.States.MID_STANCE: 0,
                                                FSM.States.LATE_STANCE: 0,
                                                FSM.States.EARLY_SWING: 0,
                                                FSM.States.LATE_SWING: 0},
                                    timeoutTime = initDefaults['walkFSM5TimeoutToWaitingDoubleSpinBox'], #s
                                    forceHysteresisTime = HardcodedDefaults.forceHysteresisTime, #s change to 0.05? 0.1?
                                    velocityHysteresisTime = HardcodedDefaults.velocityHysteresisTime, #s
                                    extAngleLimit = initDefaults['walkFSM5ExtLimitSpinBox'],
                                    flexAngleLimit = initDefaults['walkFSM5FlexLimitSpinBox'],
                                    stanceRampRate = initDefaults['walkFSM5StanceRampRateSpinBox'],
                                    swingRampRate = initDefaults['walkFSM5SwingRampRateSpinBox'],
                                    index = index)
    proportionalControlLogic = lambda index: Proportional.ProportionalControlLogic(index = index, 
                                                                     thetaMin = initDefaults['proportionalMinAngleLimitSpinBox'], 
                                                                     thetaMax = initDefaults['proportionalMaxAngleLimitSpinBox'], 
                                                                     minTorque = initDefaults['proportionalMinTorqueDoubleSpinBox'], 
                                                                     maxTorque = initDefaults['proportionalMaxTorqueDoubleSpinBox'])
    
    standingControlLogic = lambda index: Standing.StandingControlLogic(standingMode = initDefaults['standingModeComboBox'] == 0, # 0 is enabled...
                                                                             standingTorque = initDefaults['standingTorqueDoubleSpinBox'],
                                                                             slewRate = initDefaults['standingRampRateSpinBox'],
                                                                             turnOffThreshold = initDefaults['standingTurnOffThresholdSpinBox'],
                                                                             turnOnThreshold = initDefaults['standingTurnOnThresholdSpinBox'],
                                                                             index = index)

        
    return { ControlLogicEnum.FSM5: fsmControlLogic,
                ControlLogicEnum.PROPORTIONAL: proportionalControlLogic,
                ControlLogicEnum.STANDING: standingControlLogic }