from __future__ import annotations

import numpy as np
import pandas as pd
from brace.Server.Core.ComInterface import IInputCom
from brace.Server.Core.MeasurementLists import IMeasurementLists
from brace.example.exoskeleton.CANInterface2 import CANInterface2

from collections import deque
from typing import override

#calculates moving average for angular velocity  
def windowedMovingAverage(deque: deque[float], angularVelocity: float) -> float:
    """"
        Calculates the angular velocity from the values of a deque. The values are cycled
        out automatically. This creates a low pass filter for the angular velocity.

        :param deque: A window that contains a few previous values. 
        :type deque: deque[float]
        :param angularVelocity: The angular velocity for the current iteration.
        :type angularVelocity: float
        :return: The windowed angular velocity for this current iteration.
        :rtype: float
    """
    deque.append(angularVelocity)
    windowedMovingAverage = sum(deque)/len(deque)
    return windowedMovingAverage

#calculate (windowed) angular velocity and append it to corresponding vector
def calculateVelocity(angleMesAll: deque[float], deltaTime: float, deque: deque[float]) -> tuple[float, float]:
    """
        Calculates the velocity for the knee angle measurements. Both angular velocity
        and the windowed angular velocity are determined.

        :param angleMesAll: The deque containing the knee angle measurements.
        :type angleMesAll: deque[float]
        :param deltaTime: The amount of time between the control iterations.
        :type deltaTime: float
        :param deque: The deque containing the previous knee angle measurements in a window.
        :type deque: deque[float]
        :return: The tuple containing the angular velocity and the windowed angular velocity.
        :rtype: tuple[float, float]
    """
    angularVelocity: float = (angleMesAll[-1] - angleMesAll[-2]) / deltaTime
    windowedAngularVelocity = windowedMovingAverage(deque, angularVelocity)
    return angularVelocity, windowedAngularVelocity

class MeasurementLists(IMeasurementLists):
    """
        MeasurementLists for the exoskeleton.
        There are lists for knee angle, force, desired torque, corrected torque,
        the angular velocity, the window angular velocity. Data is recorded
        in these lists.
    """
    MAX_LEN = 15000
    def __init__(self):
        self.angleMesAll: deque[float] = deque(maxlen = MeasurementLists.MAX_LEN)
        self.forceMesAll: deque[float] = deque(maxlen = MeasurementLists.MAX_LEN)
        self.torqueDesAll: deque[float] = deque(maxlen = MeasurementLists.MAX_LEN)
        self.torqueInAll: deque[float] = deque(maxlen = MeasurementLists.MAX_LEN)
        self.angularVelocityAll: deque[float] = deque(maxlen = MeasurementLists.MAX_LEN)
        self.windowedAngularVelocityAll: deque[float] = deque(maxlen = MeasurementLists.MAX_LEN)
        self.calibrationOffset = 0
        self.deque: deque = deque(maxlen=4)

    @override
    def setupMeasurements(self, inputComs: list[IInputCom]) -> None:
        """
            The initial setup for the measurements which creates the first set of
            measurements.

            :param inputComs: The list of input communications interfaces that should be used
            for gathering sensor information.
            :type inputComs: list[IInputCom]
            :return: None
            :rtype: None
        """
        # Run first measurement
        angleMes, forceMes = self._readMeasurements(inputComs)
        self.angleMesAll.append(angleMes - self.calibrationOffset)
        self.forceMesAll.append(forceMes)

        # Placeholder value for angular velocity, windowed angular velocity, and torque.
        self.angularVelocityAll.append(0.0)
        self.windowedAngularVelocityAll.append(0.0)
        self.torqueDesAll.append(0.0)
        self.torqueInAll.append(0.0)

    @override
    def simulateSetupMeasurements(self) -> None:
        """
            Separate function that initializes the measurements for the first set of measurements.
            These are just set to 0 to prevent off-by-one-errors.

            :return: None
            :rtype: None
        """
        # Run first measurement
        self.angleMesAll.append(0)
        self.forceMesAll.append(0)

        # Placeholder value for angular velocity, windowed angular velocity, and torque.
        self.angularVelocityAll.append(0.0)
        self.windowedAngularVelocityAll.append(0.0)
        self.torqueDesAll.append(0.0)
        self.torqueInAll.append(0.0)

    @override
    def setCalibrationOffset(self, inputComs: list[IInputCom]) -> None:
        """
            Samples the calibration offset from the angle measurement.
            Future measurements are subtracted from this calibration offset.
            Calibration could also be sampled from previous n samples.

            :param inputComs: The list of input communications interfaces that should be used
            for gathering sensor information.
            :type inputComs: list[IInputCom]
            :return: None
            :rtype: None
        """
        angleMeasurement, _ = self._readMeasurements(inputComs)
        self.calibrationOffset = angleMeasurement

    def calculateWindowedAngularVelocity(self, inputComs: list[IInputCom], deltaTime: float) -> tuple[float, float]:
        """
            Calculates the windowed angular velocity. Only runs if the input communication is available.
            Otherwise it is measured as 0 in the lists.

            :param inputComs: List of input communications interfaces for gathering sensor information.
            :type: inputComs: list[IInputCom]
            :param deltaTime: The amount of time between control iterations.
            :type deltaTime: float
            :return: The tuple containing the angular and window angular velocity.
            :rtype: tuple[float, float]
        """
        angularVelocity, windowedAngularVelocity = 0, 0
        if inputComs[0].isComOn():
            angularVelocity, windowedAngularVelocity = calculateVelocity(self.angleMesAll,
                                                                         deltaTime,
                                                                         self.deque)

        return angularVelocity, windowedAngularVelocity

    # This probably should be part of MeasurementLists which is custom made to read in the values from 
    # this CAN Interface and I2C in the future. The calibrationOffset should be a part of MeasurementLists.
    def _readMeasurements(self, inputComs: list[IInputCom]) -> tuple[float, float]:
        angleMes, forceMes = 0, 0
        canCom = inputComs[0]
        if canCom.isComOn() and isinstance(canCom, CANInterface2):
            angleMesAll = self.angleMesAll
            forceMesAll = self.forceMesAll

            # Add offset back to match raw encoder readout (without offset) from previous measurement.
            previousAngleMesAll = angleMesAll[-1] + self.calibrationOffset if angleMesAll else self.calibrationOffset
            previousForceMesAll = forceMesAll[-1] if forceMesAll else 0.0

            encoderAngle = canCom.printEncoder()
            angleMes = encoderAngle if encoderAngle is not None else previousAngleMesAll

            fsrMes = canCom.printFSR()
            forceMes = fsrMes if fsrMes is not None else previousForceMesAll

        return angleMes, forceMes
    
    @override
    def copyMeasurements(self, i: int, measurementDataFrameToCopy: pd.DataFrame) -> None:
        """ 
            Copies the measurements from the pandas DataFrame to this MeasurementList
            This is particularly used in simulation, by simply placing the input values.

            Consider the cases:
                - Normal data (non-NaN) -> means active exo leg replaying.
                - None object -> means data is not available, the exo leg was never on during the entire session.
                - NaN data -> means either exo leg was off at this time or we use this to denote that it switched controllers.
                    - Currently you can't switch exo legs on/off during a session (may change in the future).
                    - Thus exo leg data being off would be represented by None object. NaN represents only switched controllers then.

            :param i: The iteration number that should be placed into the MeasurementList
            :type i: int
            :param measurementDataFrameToCopy: The pandas DataFrame where data should be copied from.
            :type measurementDataFrameToCopy: pandas.DataFrame
            :return: None
            :rtype: None
        """
        if not measurementDataFrameToCopy.empty:
            values = (measurementDataFrameToCopy['theta'].iat[i], measurementDataFrameToCopy['thetaDotWin'].iat[i], measurementDataFrameToCopy['fsr'].iat[i])
        else: # For none object (disabled the entire time) set to zeroes, a proper change is denoted with NaN, not a real datapoint.
            values = (0, 0, 0)

        self.angleMesAll.append(values[0])
        self.windowedAngularVelocityAll.append(values[1])
        self.forceMesAll.append(values[2])

    @override
    def runMeasurements(self, deltaTimeAll: list[float], inputComs: list[IInputCom]) -> None:
        """ 
            This evaluates the measurements from the angle encoder and FSR and copies it to the MeasurementList. 
            Returns these values back so that they can be used in the other leg's checks.

            :param deltaTimeAll: The list of times in between control loop iterations.
            :type deltaTimeAll: list[float]
            :param inputComs: The list of input communications interfaces.
            :type inputComs: list[IInputComs]
            :return: None
            :rtype: None
        """
        #read encoders (FSR and angles) and append data to vectors, if encoder output is None, use the prior reading 
        angleMes, forceMes = self._readMeasurements(inputComs)
        self.angleMesAll.append(angleMes - self.calibrationOffset)
        self.forceMesAll.append(forceMes)

        #calculate (windowed) angular velocity and append it to corresponding vector
        angularVelocity, windowedAngularVelocity = self.calculateWindowedAngularVelocity(inputComs, deltaTimeAll[-1])
        self.angularVelocityAll.append(angularVelocity)
        self.windowedAngularVelocityAll.append(windowedAngularVelocity)

    @override
    def recordOutputValues(self, outputDes: list[float], outputIn: list[float]) -> None:
        """
            Records the output values before and after safety checks to the MeasurementLists.
            
            :param outputDes: The list of outputs before safety checks.
            :type outputDes: list[float]
            :param outputIn: The list of outputs after safety checks.
            :type outputIn: list[float]
            :return: None
            :rtype: None
        """
        [torqueValue] = outputDes
        [torqueValue] = outputIn
        self.torqueDesAll.append(torqueValue)
        self.torqueInAll.append(torqueValue)

    def getAngleMeasurements(self) -> deque[float]:
        """
            Returns the deque of knee angle measurements.
            :return: Knee angle measurements
            :rtype: deque[float]
        """

        return self.angleMesAll

    def getForceMeasurements(self) -> deque[float]:
        """
            Returns the deque of FSR measurements.
            :return: FSR measurements
            :rtype: deque[float]
        """
        return self.forceMesAll

    def getTorqueDesiredMeasurements(self) -> deque[float]:
        """
            Returns the deque of torque (pre-safety check) outputs.
            :return: Torque outputs (pre-safety check)
            :rtype: deque[float]
        """
        return self.torqueDesAll

    def getTorqueInMeasurements(self) -> deque[float]:
        """
            Returns the deque of torque (post-safety check) outputs.
            :return: Torque outputs (post-safety check)
            :rtype: deque[float]
        """
        return self.torqueInAll

    def getAngularVelocityMeasurements(self) -> deque[float]:
        """
            Returns the deque of angular velocity measurements.
            :return: Angular velocity measurements
            :rtype: deque[float]
        """
        return self.angularVelocityAll

    def getWindowedAngularVelocityMeasurements(self) -> deque[float]:
        """
            Returns the windowed angular velocity measurements.
            :return: Windowed angular velocity measurements
            :rtype: deque[float]
        """
        return self.windowedAngularVelocityAll