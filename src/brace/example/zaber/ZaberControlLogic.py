from collections import deque
from typing import NamedTuple, override
from brace.example.zaber.ZaberMeasurementList import ZaberMeasurementLists
from brace.Server.Core.ControlLogic import IControlLogic
import numpy as np

class ZaberData(NamedTuple):
    position: float
    loadcell: float
    t: float #time vector

class ControlLogic:
    ZaberController = 0

class ZaberControlLogic(IControlLogic):
    DataClass = ZaberData

    def __init__(self, index: int):
        """
            :param index: The count of the respective robot that is running.
            :type index: int
        """
        super().__init__(index)
        self.positionMin = 0
        self.positionMax = 30

        self.loadcellMin = 0 # in g
        self.loadcellMax = 100 # in g

    @override
    def setup(self, **kwargs) -> None:
        """
            Initializes anything prior to running.
            :param kwargs: Keyword arguments
            :type kwargs: dict[str, All]
            :return: None
            :rtype: None
        """
        pass

    @override
    def setParameters(self, parameters: dict[str, float]) -> None:
        """
            Sets the parameters that are in the dictionary to
            the instance variables of this object.

            :param parameters: The dictionary of configuration values from a remote procedure call.
            :type parameters: dict[str, float]
            :return: None
            :rtype: Nones
        """
        # To enable changing of the parameters.
        for parameterName, parameterValues in parameters.items():
            self.__setattr__(parameterName, parameterValues)

    @override
    def getConfigurationParameters(self, formatForConfiguration: bool) -> dict[str, float | dict]:
        """
            Gets the current configuration parameters that were defined for this controller.

            :param formatForConfiguration: Whether or not this should be formatted for file saving.
            :type formatForConfiguration: bool
            :return: Dictionary of parameters in this object.
            :rtype: dict[str, float]
        """
        controllerParameters = {
            "positionMin": self.positionMin, # mm
            "positionMax": self.positionMax, # mm
            "loadcellMin": self.loadcellMin, # g
            "loadcellMax": self.loadcellMax  # g
        }
        return controllerParameters

    @override
    def getDesiredOutputValues(self, enable: bool, timeData: deque[float], deltaTime: float, currentCycleMeasurementLists: list[ZaberMeasurementLists]) -> list[float]:
        """
            Transforms the output values through a proportional response. Increased load cell
            response leads to increased actuation.

            :param enable: Whether or not device is active and running.
            :type enable: bool
            :param timeData: The time data for the the last set of cycles (the time values in s).
            :type timeData: deque[float]
            :param deltaTime: The amount of time between this iteration and the last iteration.
            :type deltaTime: float
            :param currentCycleMeasurementLists: The set of ZaberMeasurementList that can be accessed to determine the output response.
            :type currentCycleMeasurementLists: list[ZaberMeasurementLists]
            :return: The list of output responses that should be run against the actuators.
            :rtype: list[float]
        """
        posDes = 0.0
        if enable:
            measurementLists: ZaberMeasurementLists = self.getRespectiveMeasurementList(currentCycleMeasurementLists)
            loadcellG = measurementLists.getLoadCellMeasurements()[-1]
            if loadcellG <= self.loadcellMin:
                posDes = self.positionMin
            elif loadcellG >= self.loadcellMax:
                posDes = self.positionMax
            else:
                # Calculate the proportional torque within the bounds
                posDes = self.positionMin + (self.positionMax - self.positionMin) * (loadcellG - self.loadcellMin) / (self.loadcellMax - self.loadcellMin)
        return [posDes]
    
    @override
    def exportMeasurementData(self, measurementLists: ZaberMeasurementLists, index: int, isActive: bool) -> dict[str, float | int]:
        """
            Exports the MeasurementData for this cycle.

            :param measurementLists: The measurement lists for this robot whose data should be exported.
            :type measurementLists: ZaberMeasurementLists
            :param index: The current index of this robot.
            :type index: int
            :param isActive: Whether or not this robot is active (or enabled). If disabled, should return NaN maps.
            :type isActive: bool
            :return: A mapping of the attributes and the values for this current iteration.
            :rtype: dict[str, float | int]
        """
        fieldMapping = {
            "position": measurementLists.getPosMeasurements()[-1] if isActive else np.nan,
            'loadcell': measurementLists.getLoadCellMeasurements()[-1] if isActive else np.nan,
        }

        toReturn = fieldMapping
        return toReturn