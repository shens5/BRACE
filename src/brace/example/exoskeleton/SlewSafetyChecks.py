from typing import override

import brace.example.exoskeleton.BionicPowerActuatorProcess.CanHelpers as CanHelpers
from brace.example.exoskeleton.ExoMeasurementList import MeasurementLists
from brace.Server.Core import RobotHelpers
from brace.Server.Core.SafetyControl import ISafetyControl
from collections import deque

# Force to 0 if close enough
def forceCurrentDeadZone(commandCurrent: float) -> float:
    """
        Forces the current to 0 if less than 0.020 mA.

        :param commandCurrent: The current in mA to be sent to the actuator.
        :type commandCurrent: float
        :return: The current after checks.
        :rtype: float
    """
    return 0.0 if -20 <= commandCurrent <= 20 else commandCurrent # ma

def torqueToCurrent(desTorque: float) -> float:
    """
        Converts the desired torque (Nm) into a current value (mA) determined by
        Bionic Power's characteristic curve.

        :param desTorque: The amount of torque that should be sent to the actuator.
        :type desTorque: float
        :return: The amount of converted current to be used by the actuator.
        :rtype: float
    """
    #input: Nm
    #output: mA
    commandCurrent = (desTorque*0.3936 + 0.0154)*1000
    return commandCurrent

# Flexion should be considered positive (as described in the text on the GUI).
def convertTorqueConventionSign(extTorquePositive: bool, torqueIn: float) -> float:
    """
        Changes the sign of the torque convention (flexion positive vs extension positive).

        :param extTorquePositive: Whether extension is considered positive, otherwise flexion is considered positive.
        :type extTorquePositive: bool
        :param torqueIn: The torque that should have its sign potentially changed.
        :type torqueIn: float
        :return: The corrected torque value according to the actuator.
        :rtype: float
    """
    return -torqueIn if extTorquePositive else torqueIn

# Keep torque within the regulated limits.
def capTorque(torqueIn: float, torqueMinValue: float, torqueMaxValue: float) -> float:
    """
        Retains the torque within a specific minimum and maximum value.

        :param torqueIn: The desired amount of torque.
        :type torqueIn: float
        :param torqueMinValue: The most negative torque value possible by the actuator (maximum torque in one direction).
        :type torqueMinValue: float
        :param torqueMaxValue: The most positive torque value possible by the actuator (maximum torque in other direction).
        :return: The capped torque within these values.
        :rtype: float
    """
    return max(min(torqueIn, torqueMaxValue), torqueMinValue)

class SlewSafetyChecks(ISafetyControl):
    """
        This layer handles safety control for the actuator by introducing a maximum
        slew rate to the torque, current deadzone, and capping of maximum torque.
    """
    def __init__(self, extTorquePositive: bool, MAX_SLEW_RATE: float, MAX_FLEX_TORQUE: float, MAX_EXT_TORQUE: float):
        """
            :param extTorquePositive: Whether the actuator should start with torque extension positive or flexion positive.
            :type extTorquePositive: bool
            :param MAX_SLEW_RATE: Maximum slew rate of the torque that should be dealt to the actuator.
            :type MAX_SLEW_RATE: float
            :param MAX_FLEX_TORQUE: Maximum flexion torque (flexion torque is considered positive).
            :type MAX_FLEX_TORQUE: float
            :param MAX_EXT_TORQUE: Maximum extension torque (extension torque is considered negative)
            :type MAX_EXT_TORQUE: float
        """
        self.MAX_SLEW_RATE = MAX_SLEW_RATE
        self.MAX_FLEX_TORQUE = MAX_FLEX_TORQUE
        self.MAX_EXT_TORQUE = MAX_EXT_TORQUE

        self.extTorquePositive = extTorquePositive
        self.torqueMinValue = self.MAX_FLEX_TORQUE
        self.torqueMaxValue = self.MAX_EXT_TORQUE
        super().__init__()

    def setExtActuationConvention(self, extTorquePositive: bool) -> None:
        """
        Used to flip the torque such that extension is positive or negative torque. May be ignored if extension is always negative torque (flexion positive).
        This is a fairly specific problem to the actuators that we have. This is not enforced as a method in the interface.
        
        :param extTorquePositive: Flag to set to reverse the direction of actuation.
        :type extTorquePositive: bool
        :return: None
        :rtype: None
        """
        self.extTorquePositive = extTorquePositive
        # Torque definitions for min/max values. Positive extension torque means that the MAX_EXT_TORQUE should be the larger value.
        self.torqueMinValue = self.MAX_FLEX_TORQUE
        self.torqueMaxValue = self.MAX_EXT_TORQUE

    @override
    def runSafetyControl(self, measurementLists: MeasurementLists, deltaTimeAll: deque[float], outputDes: list[float]) -> list[float]:
        """
            Runs safety control on the actuators (creating a slew rate and clipping the torque to maximum values) for each
            of the torque outputs.

            :param measurementLists: The measurementLists containing old data.
            :type measurementLists: MeasurementLists
            :param deltaTimeAll: A list of the times between the control iterations.
            :type deltaTimeAll: deque[float]
            :param outputDes: A list of outputs for the actuators to be checked.
            :type outputDes: list[float]
            :return: A list of corrected outputs for the actuators.
            :rtype: list[float]
        """
        torqueInList = []
        for torque in outputDes:
            #check slew rate
            torqueIn = RobotHelpers.checkSlewRate(torque, measurementLists.torqueInAll[-1], deltaTimeAll[-1], self.MAX_SLEW_RATE)
            
            #caps amount of torque sent. See above for definitions of min and max values of torque.
            torqueIn = capTorque(torqueIn, torqueMinValue = self.torqueMinValue, torqueMaxValue = self.torqueMaxValue)
            torqueInList.append(torqueIn)
        return torqueInList

    @override
    def runOutputConversion(self, outputIn: list[float]) -> list[bytes]:
        """ 
            Converts the output values into a list of bytes that are to be written to the actuator.
            Practical conversions should be done in this case such as the convention sign change,
            forcing the dead zone current, and converting to a CAN message.
            
            :param outputIn: List of outputs to be converted to CAN messages.
            :type outputIn: list[float]
            :return: list of CAN messages that should be sent to the actuators.
            :rtype: list[byte]
        """
        torqueMsgDataList = []

        for torque in outputIn:
            commandCurrent: float = torqueToCurrent(convertTorqueConventionSign(self.extTorquePositive, torque))
        
            #forced dead zone
            commandCurrent = forceCurrentDeadZone(commandCurrent)

            torqueMsgData: bytes = CanHelpers.getTorqueMsgData_v2(commandCurrent)
            torqueMsgDataList.append(torqueMsgData)
        return torqueMsgDataList