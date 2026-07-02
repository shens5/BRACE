""" This is a separate file for helper functions that have uses in both ControlLogic level and RobotABC level which correspond to 
    a more specific vs global scope of parameters that would be used (e.g. RobotABC level enforces a maximum slew limit, while ControlLogic enforces a more local one
    depending on state).
"""
from __future__ import annotations
from collections.abc import Callable, Iterable
import itertools
from typing import NamedTuple
import numpy as np

def checkSlewRate(torqueNow: float, torquePast: float, deltaTime: float, maxSlew: float) -> float:
    """
        Function that caps the slew rate of an output value of the current iteration
        to prevent excess changes in acceleration.

        :param torqueNow: The calculated output value before checks this iteration.
        :type torqueNow: float
        :param torquePast: The output value used last iteration.
        :type torquePast: float
        :param deltaTime: The time between the last iteration and the current one in seconds.
        :type deltaTime: float
        :param maxSlew: The maximum change between the two output values per second.
        :type maxSlew: float
        :return: The output value adjusted based on the max slew rate (capped if above limit).
        :rtype: float
    """
    
    #input: Nm, Nm, sec, Nm/sec
    #output: Nm
    with np.errstate(divide='ignore', invalid='ignore'):
        try:
            Slew = (torqueNow - torquePast) / deltaTime
        except RuntimeWarning: # May trigger when deltatime is 0 (dividing by zero)
            Slew = 0 # Just set this to 0 (may trigger at the beginning during simulation)

    if abs(Slew) > maxSlew:
        if Slew > 0:
            TorqueIn = torquePast + maxSlew*deltaTime
        else:
            TorqueIn = torquePast - maxSlew*deltaTime
    else:
        TorqueIn = torqueNow
    return TorqueIn

def capTorqueFromAngle(torqueDes: float, currentAngle: float, extAngleLimit: float, flexAngleLimit: float) -> float:
    """
        Sets torque to 0 if beyond extension and flexion angle limits.
    
        :params torqueDes: The torque to use for this iteration cycle
        :type torqueDes: float
        :params currentAngle: The current angle in this iteration cycle.
        :type currentAngle: float
        :params extAngleLimit: The minimum angle limit before torque is set to 0.
        :type extAngleLimit: float
        :params flexAngleLimit: The maximum angle limit before torque is set to 0.
        :type flexAngleLimit: float
        :return: The adjusted torque after comparing between these limits.
        :rtype: float 
    """
    return torqueDes if extAngleLimit < currentAngle < flexAngleLimit else 0.0

def hysteresis2(timeData: Iterable[float], functionConditions: HysteresisParameters) -> bool:
    """
        Returns whether or not a condition has been maintained for a desired
        time before a state is changed. This is performed by looking back in time.

        :params timeData: Time data that is stored in RobotAssemblyABC.
        :type timeData: Iterable[float]
        :params functionConditions: A HysteresisParameters object that defines the conditions \
        collection, and amount of time the condition must be satisfied before considered True.
        :type functionConditions: HysteresisParameters
        :return: Whether or not the conditions have been satisifed for long enough.
        :rtype: HysteresisParameters
    """
    currentTime = timeData[-1]
    hysteresisTime = functionConditions.hysteresisTime

    i = -1
    while ((i - 1) > -(len(timeData) + 1)) and currentTime - timeData[i - 1] <= hysteresisTime:
        i = i - 1

    measurementCollectionLength = len(functionConditions.measurementCollection)
    # Empirically faster than numpy eq. (even despite vectorization? Takes half the time)
    iterationSlice = itertools.islice(functionConditions.measurementCollection, 
                            measurementCollectionLength + i, measurementCollectionLength - 1)
    testCondition = [functionConditions.lambdaCondition(i) for i in iterationSlice]
    return all(testCondition)

def hysteresisMultiple(timeData: Iterable[float], functionConditions: list[HysteresisParameters]) -> bool:
    """
        Checks multiple hysteresis conditions to verify all conditions are true.

        :params timeData: Time data that is stored in RobotAssemblyABC
        :type timeData: Iterable[float]
        :params functionConditions: A list of HysteresisParameters whose conditions should be checked.
        :type functionConditions: list[HysteresisParameters]
        :return: Whether or not all hysteresis conditions are satisfied.
        :rtype: bool
    """
    hysteresisTrue = True
    for hysteresisParameter in functionConditions:
        hysteresisTrue = hysteresisTrue and hysteresis2(timeData, hysteresisParameter)
        if not hysteresisTrue:
            break
    return hysteresisTrue

class HysteresisParameters(NamedTuple):
    """
        HysteresisParameters are for evaluating all the values of a certain measurement (up to a certain hysteresisTime) back in time.
        In order for hysteresis to be considered true, all values have to return true when evaluated by the lambdaCondition.
        A successful hysteresis signals long enough stability to switch a state.

        NamedTuple that contains
            lambdaCondition - a callable that contains a float and returns a bool (for evaluating across all values in measurementCollection).
            measurementCollection - an iterable of floats in the measurementList that should be measured against. Values checked are paired with time iterable.
            hysteresisTime - the length of how long hysteresis should be checked for previous measurement values. 
    """
    lambdaCondition: Callable[[float], bool]
    measurementCollection: Iterable[float]
    hysteresisTime: float