
from abc import abstractmethod
from collections.abc import Iterable
from typing import Any
from brace.Server.Core.MeasurementLists import IMeasurementLists

class ISafetyControl():
    """ Layer that handles constraints for safety and conversions (bytestrings and other messages) for output actuators. """

    @abstractmethod
    def runSafetyControl(self, measurementLists: IMeasurementLists, deltaTimeAll: Iterable[float], outputDes: Iterable[float]) -> Iterable[float]:
        """
        Runs safety control on the outputDes and returns out a list of outputs within safety boundaries.
        
        :param measurementLists: MeasurementList for this leg (and safety check). May use this for determining safety parameters.
        :type measurementLists: IMeasurementLists
        :param deltaTimeAll: An iterable containing the times between timesteps.
        :type deltaTimeAll: Iterable[float]
        :param outputDes: An iterable returned from the ControlLogic for desired output values.
        :type outputDes: Iterable[float]
        :return: An iterable of same size from outputDes containing altered outputDes values (called outputIn).
        :rtype: Iterable[float]
        """
        pass

    @abstractmethod
    def runOutputConversion(self, outputIn: Iterable[float]) -> Iterable[Any]:
        """
        Translates the outputIn values to format accepted by the output communications interfaces. 
        
        :param outputIn: An iterable containing the outputIn values from runSafetyControl
        :type outputIn: Iterable[float]
        :return: An iterable containing the converted outputIn commands.
        :rtype: Iterable[Any]
        """
        pass