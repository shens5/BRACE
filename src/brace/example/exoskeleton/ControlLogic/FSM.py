from __future__ import annotations
from collections import deque
from enum import IntEnum
from typing import NamedTuple
import time

from brace.example.exoskeleton.ExoMeasurementList import MeasurementLists
from brace.Server.Core.ControlLogic import IControlLogic
import brace.Server.Core.RobotHelpers as RobotHelpers
from typing import override
import numpy as np
import logging
logger = logging.getLogger("logger")

class States(IntEnum):
    """
        States for 5-state FSM designated for segmenting the gait phase.
    """
    WAITING = 0
    EARLY_STANCE = 1
    MID_STANCE = 2
    LATE_STANCE = 3
    EARLY_SWING = 4
    LATE_SWING = 5

#will hold the most recent sample of corresponding vector to be put into queue
class FSM5(NamedTuple):
    """
        NamedTuple that holds information for this control iteration.
        All NamedTuples should have at the minimum "t" for time.
        L and R are suffixed at the end for left and right data values.
        All values that are used in the IControlLogic class should be included
        such that it may be replicated in simulation.
    """
    thetaL: float # Knee angle
    thetaR: float
    fsrL: float # FSR values
    fsrR: float
    thetaDotWinL: float # Windowed angular velocity
    thetaDotWinR: float
    stateL: float # FSR State (enum)
    stateR: float
    torqueDesL: float # Torque before safety checks
    torqueDesR: float
    torqueInL: float # Torque after safety checks
    torqueInR: float
    t: float #time vector

class FSMControlLogic(IControlLogic):
    """
        This is the IControlLogic that handles the control logic for the finite state
        machine based walking. It undergoes one pass of state determination based on
        sensor data, followed by hysteresis which debounces the state change,
        and deadzone which maintains the state for a minimum period of time before another
        state change could be done.

        If there is no state change for a certain period of time, then the state is timed
        out to the WAITING state, which is maintained for as long as the leg is not moved
        past the windowed velocity threshold. 
    """
    DataClass = FSM5

    def __init__(self, forceSensorThresholdInitialContact: int, forceSensorThresholdSwing: int, 
                 deadZoneTime: float, velocityEarlyToMidStanceThreshold: int, velocityMidToLateStanceThreshold: int, 
                 velocityEarlyToLateSwingThreshold: int, stateTorques: dict[States, float], timeoutTime: float, 
                 forceHysteresisTime: float, velocityHysteresisTime: float, extAngleLimit: int, flexAngleLimit: int, 
                 stanceRampRate: int, swingRampRate: int, index: int):
        
        """
            :param forceSensorThresholdInitialContact: The initial contact force threshold that must be reached to
            get to stance phase. Measured in mV.
            :type forceSensorThresholdInitialContact: int
            :param forceSensorThresholdSwing: The swing force threshold that must be crossed to reach the swing phase. Measured
            in mV.
            :type forceSensorThresholdSwing: int
            :param deadZoneTime: The amount of time that a state must be in before another state change can be performed.
            Measured in s.
            :type deadZoneTime: float
            :param velocityEarlyToMidStanceThreshold: The velocity threshold to get from early to mid stance (must be above).
            :type velocityEarlyToMidStanceThreshold: int
            :param velocityMidToLateStanceThreshold: The velocity threshold to get from mid to late stance (must be below).
            :type velocityMidToLateStanceThreshold: int
            :param velocityEarlyToLateSwingThreshold: The velocity threshold to get from early to late swing (must be above)
            :type velocityEarlyToLateSwingThreshold: int
            :param stateTorques: The lookup table for torque values given a state.
            :type stateTorques: stateTorques: dict[States, float]
            :param timeoutTime: The timeout to the WAITING state in seconds.
            :type timeoutTime: float
            :param forceHysteresisTime: The initialized hysteresis period for checking force (must hold force for this long)
            :type forceHysteresisTime: float
            :param velocityHysteresisTime: The initialized hysteresis period for checking velocity (must hold velocity for this long)
            :type velocityHysteresisTime: float
            :param extAngleLimit: The extension angle limits, will cut off torque if below this angle.
            :type extAngleLimit: int
            :param flexAngleLimit: The flexion angle limits, will cut off torque if above this angle.
            :type flexAngleLimit: int
            :param stanceRampRate: The prescribed torque ramp rate for states in stance.
            :type stanceRampRate: int
            :param swingRampRate: The prescribed torque ramp rate for states in swing.
            :type swingRampRate: int
            :param index: The referencing index for this leg in the RobotAssemblyABC. May be used in determining left/right.
            :type index: int
        """
        super().__init__(index = index)
        self.forceSensorThresholdInitialContact = forceSensorThresholdInitialContact
        self.forceSensorThresholdSwing = forceSensorThresholdSwing

        self.stateAll: deque[States] = deque(maxlen = MeasurementLists.MAX_LEN) #stores all states 

        # Dictionary to configure the torques for each state.
        self.stateTorques = stateTorques

        self.state: States = States.WAITING #stores only most recent state
        self.timeOfStateChange: float = 0.0 #previously gaitStateTime

        self.deadZoneTime: float = deadZoneTime
        self.timeoutTime: float = timeoutTime
        
        self.forceHystesisTime = forceHysteresisTime
        self.velocityHysteresisTime = velocityHysteresisTime

        self.extAngleLimit = extAngleLimit
        self.flexAngleLimit = flexAngleLimit

        self.stanceRampRate = stanceRampRate
        self.swingRampRate = swingRampRate

        self.velocityEarlyToMidStanceThreshold = velocityEarlyToMidStanceThreshold
        self.velocityMidToLateStanceThreshold = velocityMidToLateStanceThreshold
        self.velocityEarlyToLateSwingThreshold = velocityEarlyToLateSwingThreshold

        self.SWING_STATES = {States.EARLY_SWING, States.LATE_SWING}
        self.waitingVelocityThreshold = 0.01

    @override
    def setup(self, **kwargs) -> None:
        """
            Setup to be done outside of init, but before the full control iteration.

            :param kwargs: Keyword arguments to be used.
            :type kwargs: dict[str, Any]
            :return: None
            :rtype: None
        """
        self.timeOfStateChange = time.perf_counter()
        self.simulatedSetup(**kwargs)

    @override
    def simulatedSetup(self, **kwargs) -> None:
        """
            Setup for the simulator to be done outside of init, but before the full control iteration. 
            These are typically non-time related setup functions. 

            :param kwargs: Keyword arguments to be used.
            :type kwargs: dict[str, Any]
            :return: None
            :rtype: None
        """
        self.stateAll.append(self.state) # Add one instance of the WAITING state to the beginning

    @override
    def setParameters(self, parameters: dict[str, float]) -> None:
        """
            Sets instance variables parameters based on what was sent
            from the client to the remote.

            :param parameters: The parameters to set.
            :type parameter: dict[str, float]
            :return: None
            :rtype: None
        """
        # To enable changing of the parameters.
        # forceSensorThresholdInitialContact, forceSensorThresholdSwing
        # deadZoneTime, stateTorques, timeoutTime
        for parameterName, parameterValues in parameters.items():
            self.__setattr__(parameterName, parameterValues)

    @override
    def getConfigurationParameters(self, formatForConfiguration: bool) -> dict[str, float | dict]:
        """
            Returns the configuration parameters to be used in updating the GUI or retrieved
            for saving into the save files.
            
            :param formatForConfiguration: Set to True if saving for a save file.
            :type formatForConfiguration: bool
            :return: The parameter configuration for the control law.
            :rtype: dict[str, float | dict]
        """
        if formatForConfiguration:
            stateTorques = {state.name: torqueValue for state, torqueValue in self.stateTorques.items()}
        else:
            stateTorques = self.stateTorques
        controllerParameters = {
            "forceSensorThresholdInitialContact": self.forceSensorThresholdInitialContact, # mV
            "forceSensorThresholdSwing": self.forceSensorThresholdSwing, # mV
            "deadZoneTime": self.deadZoneTime, # s
            'velocityEarlyToMidStanceThreshold': self.velocityEarlyToMidStanceThreshold, # deg/s
            'velocityMidToLateStanceThreshold': self.velocityMidToLateStanceThreshold, # deg/s
            'velocityEarlyToLateSwingThreshold': self.velocityEarlyToLateSwingThreshold, # deg/s
            "stateTorques": stateTorques,
            "timeoutTime": self.timeoutTime, # s
            "extAngleLimit": self.extAngleLimit, # degrees
            "flexAngleLimit": self.flexAngleLimit, # degrees,
            "stanceRampRate": self.stanceRampRate, # Nm/s
            "swingRampRate": self.swingRampRate # Nm/s
        }
        return controllerParameters
    
    def FSM(forceMesAll: deque[float], windowedAngularVelocityAll: deque[float], previousState: States, 
            forceSensorThresholdInitialContact: float, forceSensorThresholdSwing: float, 
            velocityEarlyToMidStanceThreshold: int, velocityMidToLateStanceThreshold: int, velocityEarlyToLateSwingThreshold: int) -> States:
        """
            The main FSM for this control law. There are two 
            phases: the initial set of if-else statements juggle stance and swing,
            while the second set check the sub-phases of the FSM.

            :param forceMesAll: The deque of FSR measurements that were collected in the MeasurementLists
            :type forceMesAll: collections.deque[float]
            :param windowedAngularVelocityAll: The deque of windowed angular velocity measurements in the MeasurementLists.
            :type windowedAngularVelocityAll: collections.deque[float]
            :param previousState: States
            :type previousState: The previous state determined in the last control iteration.
            :param forceSensorThresholdInitialContact: The force threshold for entering stance.
            :type forceSensorThresholdInitialContact: float
            :param forceSensorThresholdSwing: The force threshold for entering swing.
            :type forceSensorThresholdSwing: float
            :param velocityEarlyToMidStanceThreshold: The velocity threshold for going from early to mid stance.
            :type velocityEarlyToMidStanceThreshold: int
            :param velocityMidToLateStanceThreshold: The velocity threshold for going from mid to late stance.
            :type velocityMidToLateStanceThreshold: int
            :param velocityEarlyToLateSwingThreshold: The velocity threshold for going from early to late swing.
            :return: The current state (without corrections) for this cycle.
            :rtype: States
        """
        # Note that any comparison operation against a NaN equals False. 

        state = previousState
        # If previous was swing (either)
        #   if flexing (above threshold)
        
        if forceMesAll[-1] >= forceSensorThresholdInitialContact:
            isStance = True
            isSwing = False
        elif forceMesAll[-1] <= forceSensorThresholdSwing:
            isStance = False
            isSwing = True
        else:
            isStance = previousState in {States.EARLY_STANCE, States.MID_STANCE, States.LATE_STANCE}
            isSwing = not isStance

        if isSwing:
            if (windowedAngularVelocityAll[-1] <= velocityEarlyToLateSwingThreshold):
                state = States.LATE_SWING
            else:
                state = States.EARLY_SWING
        elif isStance:
            if previousState not in {States.MID_STANCE, States.LATE_STANCE} and not windowedAngularVelocityAll[-1] <= velocityEarlyToMidStanceThreshold:
                state = States.EARLY_STANCE
            else:
                if windowedAngularVelocityAll[-1] <= velocityEarlyToMidStanceThreshold:
                    state = States.MID_STANCE
                elif windowedAngularVelocityAll[-1] >= velocityMidToLateStanceThreshold:
                    state = States.LATE_STANCE
            
        return state

    #initiate dead period in exo - ensures at least 150 ms passes before state change.
    def deadZone(deadZoneTime: float, tentativeCurrentState: States, previousState: States, currentTime: float, timeOfStateChange: float) -> States:
        """
            Determines whether enough time elapsed since the last state change to determine whether
            it is able to change states again.

            :param deadZoneTime: The amount of time that the state must be in before another state change.
            :type deadZoneTime: float
            :param tentativeCurrentState: The state before corrections.
            :type tentativeCurrentState: States
            :param previousState: The previous state of this control law.
            :type previousState: States
            :param currentTime: The current time of this iteration (in s).
            :type currentTime: float
            :param timeOfStateChange: The amount of time that the state has been maintained.
            :type timeOfStateChange: float
            :return: The corrected state after measuring deadzone: either tentativeCurrentState or previousState.
            :rtype: States
        """
        correctedState = tentativeCurrentState
        timeSinceStateChange = currentTime - timeOfStateChange

        if timeSinceStateChange < deadZoneTime : #originally 100 ms
            correctedState = previousState
        return correctedState

    
    def timeout(timeoutTime: float, tentativeCurrentState: States, currentTime: float, timeOfStateChange: float) -> States:
        """
            If in one state for a time period greater than timeoutTime, state will timeout to WAITING.

            :param timeoutTime: Time to elapse in a single state for it to timeout to WAITING.
            :type timeoutTime: float
            :param tentativeCurrentState: The determined state before corrections.
            :type tentativeCurrentState: States
            :param currentTime: The current time of this control iteration.
            :type currentTime: float
            :param timeOfStateChange: The time since the last state change.
            :type timeOfStateChange: float
            :return: The corrected state: either the tentativeCurrentState or WAITING.
            :rtype: States
        """
        correctedState = tentativeCurrentState
        timeSinceStateChange = currentTime - timeOfStateChange

        if timeSinceStateChange >= timeoutTime: #if time in state is longer than timeout time
            correctedState = States.WAITING
        return correctedState
    
    # All of the ones above are pure functions. The ones following mutate logic state.
    def transitionStateMachine(self, enable: bool, previousState: States, 
                               windowedAngularVelocityAll: deque[float], forceMesAll: deque[float]) -> States:
        """
            Transitions the state machine based on the FSM rules. Leaves the state at WAITING
            if disabled.

            :param enable: Whether this leg is enabled. 
            :type enable: bool
            :param previousState: The previous state of the control iteration.
            :type previousState: States
            :param windowedAngularVelocityAll: The deque of windowed angular velocity values.
            :type windowedAngularVelocityAll: deque[float]
            :param forceMesAll: The deque of FSR values.
            :type forceMesAll: deque[float]
            :return: The tentative state before corrections.
            :rtype: States
        """
        tentativeCurrentState = States.WAITING
        if enable: 
            tentativeCurrentState = FSMControlLogic.FSM(forceMesAll, windowedAngularVelocityAll, 
                             previousState, self.forceSensorThresholdInitialContact, self.forceSensorThresholdSwing, 
                             self.velocityEarlyToMidStanceThreshold, self.velocityMidToLateStanceThreshold, self.velocityEarlyToLateSwingThreshold)
        return tentativeCurrentState
    
    def prehysteresis(tentativeState: States, forceHysteresisTime: float, velocityHysteresisTime: float, forceSensorThresholdInitialContact: float,
                       forceSensorThresholdSwing: float, velocityEarlyToMidStanceThreshold: float, velocityMidToLateStanceThreshold: float, velocityEarlyToLateSwingThreshold: float,
                       measurementList: MeasurementLists) -> RobotHelpers.HysteresisParameters:
        """
            Sets up the hysteresis conditions for each of the states. Threshold crossing over must maintain 
            above 95% of the threshold value for the set hysteresis time, while threshold crossings under
            must maintain below 105% of the threshold value for the hysteresis times. WAITING has no hysteresis state.

            :param tentativeState: The state before corrections.
            :type tentativeState: States
            :param forceHysteresisTime: The minimum amount of time that the force has to be within window for state change.
            :type forceHysteresisTime: float
            :param velocityHysteresisTime: The minimum amount of time that the angular velocity has to be within window for state change.
            :type velocityHysteresisTime: float
            :param forceSensorThresholdInitialContact: The force threshold for stance.
            :type forceSensorThresholdInitialContact: float
            :param forceSensorThresholdSwing: The force threshold for swing.
            :type forceSensorThresholdSwing: float
            :param velocityEarlyToMidStanceThreshold: The velocity threshold for early to mid stance.
            :type velocityEarlyToMidStanceThreshold: float
            :param velocityMidToLateStanceThreshold: The velocity threshold for mid to late stance.
            :type velocityMidToLateStanceThreshold: float
            :param velocityEarlyToLateSwingThreshold: The velocity threshold for early to late swing.
            :type velocityEarlyToLateSwingThreshold: float
            :param measurementList: The measurement list that should be checked for previous values.
            :type measurementList: MeasurementLists
            :return: A set of Hysteresis parameters that need to be checked this cycle to check validity of state change.
            :rtype: RobotHelpers.HysteresisParameters
        """
        functionConditions = {
            States.WAITING: RobotHelpers.HysteresisParameters(lambda _: True, [0], 0), # Just let it go to waiting without check. Contains placeholder
            States.EARLY_STANCE: RobotHelpers.HysteresisParameters(lambda force: force >= 0.95 * forceSensorThresholdInitialContact, 
                                                      measurementList.forceMesAll, forceHysteresisTime),
            States.MID_STANCE: RobotHelpers.HysteresisParameters(lambda velocity: velocity <= 1.05 * velocityEarlyToMidStanceThreshold, 
                                                    measurementList.windowedAngularVelocityAll, velocityHysteresisTime),
            States.LATE_STANCE: RobotHelpers.HysteresisParameters(lambda velocity: velocity >= 0.95 * velocityMidToLateStanceThreshold, 
                                                     measurementList.windowedAngularVelocityAll, velocityHysteresisTime), 
            States.EARLY_SWING: RobotHelpers.HysteresisParameters(lambda force: force <= 1.05 * forceSensorThresholdSwing, 
                                                     measurementList.forceMesAll, forceHysteresisTime),
            States.LATE_SWING: RobotHelpers.HysteresisParameters(lambda velocity: velocity <= 1.05 * velocityEarlyToLateSwingThreshold, 
                                                    measurementList.windowedAngularVelocityAll, velocityHysteresisTime)
        }
        return functionConditions[tentativeState]
    
    @override
    def getDesiredOutputValues(self, enable: bool, timeData: deque[float], deltaTime: float, currentCycleMeasurementLists: list[MeasurementLists]) -> list[float]:
        """
            This function should determine any state changes and return a set of output values that correspond
            to how the output should change.

            :param enable: Whether the leg is enabled or disabled.
            :type enable: bool
            :param timeData: The deque of previous (and current) time datapoints measured (in s).
            :type timeData: collections.deque[float]
            :param deltaTime: The amount of time this control iteration and the previous.
            :type deltaTime: float
            :param currentCycleMeasurementLists: The MeasurementLists from the other robots that may be used in conjunction with the 
            current cycle to determine the output state and values.
            :type currentCycleMeasurementLists: list[MeasurementLists]
            :return: List of output values that should be sent to actuators before safety checks.
            :rtype: list[float]
        """
        measurementLists: MeasurementLists = self.getRespectiveMeasurementList(currentCycleMeasurementLists)
        previousState = self.stateAll[-1]
        currentTime = timeData[-1]

        # Finds the transition based on event; otherwise keeps same state
        # Switch flag waiting if no change.
        tentativeCurrentState = self.transitionStateMachine(enable = enable,
                                                                             previousState = previousState, 
                                                                             windowedAngularVelocityAll = measurementLists.windowedAngularVelocityAll, 
                                                                             forceMesAll = measurementLists.forceMesAll)      

        #ensures no state change unless hysteresisTime (10ms) has passed and FSR reading has stayed above percentage of threshold the hysteresisTime
        if tentativeCurrentState != previousState:
            hysteresisParameters = FSMControlLogic.prehysteresis(tentativeCurrentState,
                                           self.forceHystesisTime,
                                           self.velocityHysteresisTime,
                                           self.forceSensorThresholdInitialContact,
                                           self.forceSensorThresholdSwing,
                                           self.velocityEarlyToMidStanceThreshold,
                                           self.velocityMidToLateStanceThreshold,
                                           self.velocityEarlyToLateSwingThreshold,
                                           measurementLists)
            
            if RobotHelpers.hysteresis2(timeData, hysteresisParameters):
                tentativeHysteresisCurrentState = tentativeCurrentState
            else:
                tentativeHysteresisCurrentState = previousState
        else: 
            tentativeHysteresisCurrentState = tentativeCurrentState
        
        if tentativeHysteresisCurrentState != previousState:
            #ensures no state change until deadZoneTime (100ms) has passed
            tentativeCheckedCurrentState = FSMControlLogic.deadZone(self.deadZoneTime, tentativeHysteresisCurrentState, previousState, currentTime, self.timeOfStateChange)

            #  Heuristic to keep it in the waiting state until something else happens (velocity within a static threshold).
            if previousState == States.WAITING and abs(measurementLists.windowedAngularVelocityAll[-1]) <= self.waitingVelocityThreshold:
                tentativeCheckedCurrentState = States.WAITING
        else:
            #assigns state to WAITING if state hasn't changed for time period longer than timeoutTime (1s)
            tentativeCheckedCurrentState = FSMControlLogic.timeout(self.timeoutTime, tentativeHysteresisCurrentState, currentTime, self.timeOfStateChange)
        
        #assigns final checked state to self.state and assigns torque value based on self.state
        self.state = tentativeCheckedCurrentState
        torqueDes = self.stateTorques[self.state] # Determine the desired torque after all of the possible recalls back to previous state.

        maxSlewRate = self.swingRampRate if self.state in self.SWING_STATES else self.stanceRampRate
        slewTorqueDes = RobotHelpers.checkSlewRate(torqueDes, measurementLists.torqueInAll[-1], deltaTime, maxSlewRate)

        #if the state changes, reset timeOfStateChange
        if self.state != previousState:
            self.timeOfStateChange = currentTime

        self.stateAll.append(self.state) # If not changed, it just appends the WAITING state

        cappedTorqueDes = RobotHelpers.capTorqueFromAngle(slewTorqueDes, currentAngle = measurementLists.angleMesAll[-1], 
                                                          extAngleLimit = self.extAngleLimit, flexAngleLimit = self.flexAngleLimit)
        
        return [cappedTorqueDes]
    
    @override
    def exportMeasurementData(self, measurementLists: MeasurementLists, index: int, isActive: bool) -> dict[str, float | int]:
        """
            Exports the measurement data in the form of a map. If the leg is not active, then
            the mapping should use numpy NaNs instead of using the actual value. This denotes that
            the leg is inactive in all graphs. All input data used in the state and output calculations
            should be exported to enable working simulation.

            :param measurementLists: The current measurementList used by this control logic.
            :type measurementList: MeasurementLists
            :param index: The index of the current leg with respect to the RobotAssemblyABC. This can be used
            to determine left and right positioning.
            :type index: int
            :param isActive: Whether this leg is active.
            :type isActive: bool
            :return: Dictionary containing the attributes and values from the NamedTuple definition
            of the DataClass of the control logic object.
            :rtype: dict[str, float | int]
        """
        fieldMapping = {
            "theta": measurementLists.angleMesAll[-1] if isActive else np.nan,
            "fsr": measurementLists.forceMesAll[-1] if isActive else np.nan,
            "thetaDotWin": measurementLists.windowedAngularVelocityAll[-1] if isActive else np.nan,
            "state": self.stateAll[-1] if isActive else np.nan,
            "torqueDes": measurementLists.torqueDesAll[-1] if isActive else np.nan,
            "torqueIn": measurementLists.torqueInAll[-1] if isActive else np.nan
        }

        toReturn = {}
        if index == 0:
            templateName = "{0}L"
            
        else:
            templateName = "{0}R"

        for fieldName, value in fieldMapping.items():
            toReturn[templateName.format(fieldName)] = value
        return toReturn