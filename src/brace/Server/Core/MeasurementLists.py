from __future__ import annotations
from abc import abstractmethod
from typing import Iterable
import pandas as pd

from brace.Server.Core.ComInterface import IInputCom
class IMeasurementLists():
    """
    A container object that retains generic sensor data and output data. These datapoints are intended to be
    aligned in length with the time stored in RobotAssemblyABC. Thus specific control logic state should ideally be held
    in the IControlLogic class itself. The data stored in this container is passed as a parameter for IControlLogic
    and is used in exporting data for the iteration.
    """
    def __init__(self) -> None:
        pass

    @abstractmethod
    def setupMeasurements(self) -> None:
        """
        Runs the first iteration. Where values don't have instantaneous meaning (like velocity), fill with 0s or NaNs.
        :return: None
        :rtype: None
        """
        pass

    @abstractmethod
    def simulateSetupMeasurements(self) -> None:
        """
        Runs the first iteration during a simulated run. Where values don't have instantaneous meaning (like velocity), fill with 0s or NaNs.
        :return: None
        :rtype: None
        """
        pass

    @abstractmethod
    def runMeasurements(self, deltaTimeAll: Iterable[float], inputComs: Iterable[IInputCom]) -> None:
        """
        Reads input measurements for a cycle using the input interfaces set at the RobotABC level. Should also perform any
        derived measurements.
        
        :param deltaTimeAll: an iterable containing the times between timesteps.
        :type deltaTimeAll: Iterable[float]
        :param inputComs: an iterable containing the input communciations interfaces for receiving measurements.
        :type inputComs: Iterable[IInputCom]
        :return: None
        :rtype: None
        """
        pass

    @abstractmethod
    def copyMeasurements(self, i: int, measurementDataFrameToCopy: pd.DataFrame) -> None:
        """
        Used for copying measurements from one master list to the measurements for offline logic controller evaluation.
        This is done clockstep to clockstep with the integer i. All the relevant inputs should be copied, but leave out any outputs.
        
        :param i: the step at which a measurement is copied into this measurementList
        :type i: int
        :param measurementListToCopy: A master dataframe by which to copy input measurements from.
        :type measurementListToCopy: pandas.DataFrame
        :return: None
        :rtype: None
        """
        pass

    @abstractmethod
    def recordOutputValues(self, outputDes: Iterable[float], outputIn: Iterable[float]) -> None:
        """
        The torque values before and after safety controls are passed in. This may be recorded into the measurement list. 
        Otherwise, keep this as pass. 
        
        :param outputDes: An iterable of one or more actual torque desired (if there is more than one actuator)
        :type outputDes: Iterable[float]
        :param outputIn: An iterable of one or more actual torque actuation values (if there is more than one actuator)
        :type outputIn: Iterable[float]
        :return: None
        :rtype: None
        """
        pass

    @abstractmethod
    def setCalibrationOffset(self, inputComs: Iterable[IInputCom]) -> None:
        """
        Zeroes the measurements at the current value by creating an offset. This may be done for some or all of the measurements. 
        
        :param inputComs: An iterable of the input interfaces for getting input measurements.
        :type inputComs: Iterable[IInputCom]
        :return: None
        :rtype: None
        """
        pass