from typing import Any, override
from brace.example.zaber.ZaberMeasurementList import ZaberMeasurementLists
from brace.Server.Core import RobotHelpers
from brace.Server.Core.SafetyControl import ISafetyControl

class ZaberTransform(ISafetyControl):
    def __init__(self, invert: bool):
        self.invert = invert
        self.MAX_SLEW_RATE = 60 # 60mm/s
        self.MIN_RANGE = 0
        self.MAX_RANGE = 30
        super().__init__()

    def setExtActuationConvention(self, extTorquePositive: bool) -> None:
        """
            Inverts the actuation direction. Toggles between most extended is considered zero
            and the most retracted position being considered zero.
            
            :param extTorquePositive: Toggles the invert position.
            :type extTorquePositive: bool
            :return: None
            :rtype: None
        """
        self.invert = extTorquePositive

    @staticmethod
    def capPosition(positionIn: float, positionMaxValue: float, positionMinValue: float) -> float:
        """
            Caps the position of the actuator to the constrains, 0 and maximum 30.

            :param positionIn: The position to cap.
            :type positionIn: float
            :param positionMaxValue: The maximum position value
            :type positionMaxValue: float
            :param positionMinValue: The minimum position value. 
            :type positionMinValue: float
        """
        return max(min(positionIn, positionMaxValue), positionMinValue)

    @override
    def runSafetyControl(self, measurementLists: ZaberMeasurementLists, deltaTimeAll: list[float], posDes: list[float]) -> list[float]:
        """
            This runs the safety control, slewing the actuator to prevent overexceeding limits, and also caps the position
            of the actuator.

            :param measurementLists: The measured values in this robot.
            :type measurementLists: ZaberMeasurementLists
            :param deltaTimeAll: The list of times in between iterations.
            :type deltaTimeAll: list[float]
            :param posDes: The previous positions that this actuator has gone through.
            :type posDes: list[float]
            :return: A list of actuator positions (in case of one, only one is in the list)
            :rtype: list[float]
        """
        positionInList = []
        for position in posDes:
            #check slew rate
            positionIn = RobotHelpers.checkSlewRate(position, measurementLists.getPosMeasurements()[-1], deltaTimeAll[-1], self.MAX_SLEW_RATE)
            
            #caps position sent.
            positionIn = ZaberTransform.capPosition(positionIn, self.MIN_RANGE, self.MAX_RANGE)
            positionInList.append(positionIn)
        return positionInList

    @override
    def runOutputConversion(self, outputIn: list[float]) -> list[Any]:
        """
            Converts the position to the desired form, inverting it as necessary.
            
            :param outputIn: The raw output positions before any conversion.
            :type outputIn: list[float]
            :return: The converted values of the position
            :rtype: list[Any]
        """
        positionConv = [position if not self.invert else self.MAX_RANGE - position for position in outputIn]
        return positionConv