from abc import abstractmethod
from collections.abc import Iterable, Sequence
from typing import Any, NamedTuple
from brace.Server.Core.MeasurementLists import IMeasurementLists
class IControlLogic():
    """
        Interface for each control logic class that defines the discrete behavior to run.
        Each IControlLogic should have a DataClass which is a NamedTuple. </br>
        Notably, one of these attributes has to be t, which represents the time value for that particular datapoint.
        The other NamedTuple elements have to be positioned in the 
        same order that the dataset lines were added in initial configuration of the subplots
        (and must follow row-major order. E.g. for a figure with subplots of size 5,2, 
        starts with subplot 0,0; 0,1; 1,0; 1,1; 2,0; 2,1... 5,1).
    """
    DataClass: NamedTuple = None

    def __init__(self, index: int):
        """
            :param index: The current index for the leg this logic controller belongs to.
            :type index: int
        """
        self.index = index

    def getRespectiveMeasurementList(self, currentCycleMeasurementList: Sequence[IMeasurementLists]) -> IMeasurementLists:
        """
            A helper method to get the respective measurement list for the leg it belongs to 
            (assuming that measurements and legs are linked pairwise).
            
            :param currentCycleMeasurementList: A container with MeasurementLists (all of the measurements).
            :type currentCycleMeasurementList: Sequence[IMeasurementLists]
            :return: The current leg's MeasurementList. 
            :rtype: IMeasurementLists
        """
        return currentCycleMeasurementList[self.index]
     
    @abstractmethod
    def setup(self, **kwargs: dict[str, Any]) -> None:
        """
            To be run on the "first" time before any real measurements are performed. 
            This includes having any placeholder values before execution.
            
            :param kwargs: Dictionary pairing for any keywords in initialization.
            :type kwargs: dict[str, Any]
            :return: None
            :rtype: None
        """
        pass

    @abstractmethod
    def simulatedSetup(self, **kwargs: dict[str, Any]) -> None:
        """
            To be run on the "first" time before any real measurements are performed, as run by simulator. 
            This includes having any placeholder values before execution.
            
            :param kwargs: Dictionary pairing for any keywords in initialization.
            :type kwargs: dict[str, Any]
            :return: None
            :rtype: None
        """
        pass

    @abstractmethod
    def setParameters(self, parameters: dict[str, float]) -> None:
        """
            Used for modifying the parameters of a certain ControlLogic. Parameters are stored in dictionary format.
            Some input validation may be done at this step.
            
            :param parameters: Dictionary of key-value pairs that are used to update the instance variables used in the logic controller.
            :type parameters: dict[str, float]
            :return: None
            :rtype: None
        """
        pass

    @abstractmethod
    def getConfigurationParameters(self, formatForConfiguration: bool) -> dict[str, float | dict]:
        """
            Used for retrieving a subset of relevant parameters that may be modified in a ControlLogic. Should return a dictionary of a subset of values.
            
            :param formatForConfiguration: A boolean that indicates whether or not the return configuration 
                should be formatted for the data file configuration (e.g. dictionary with strings as 
                keys instead of Enums, to preserve names). Should be true if for file (such as exported 
                data trial configuration), false for regular GUI management.
            :type formatForConfiguration: bool
            :return: A dictionary of relevant values that are used by the ControlLogic (that may vary for each person).
            :rtype: dict[str, float | dict]
        """
        pass

    @abstractmethod
    def getDesiredOutputValues(self, enable: bool, timeData: Iterable[float], deltaTime: float, currentCycleMeasurementLists: Iterable[IMeasurementLists]) -> Iterable[float]:
        """
            Intended to run the entirety of the control logic for the particular controller type including any state change. 
            Should return a parameter indicating numerical value that represents actuator movement (such as actuator position or torque).
            
            :param enable: A flag to determine "active" (set to defaults otherwise). Will still run otherwise.
            :type enable: bool
            :param timeData: An iterable of timesteps.
            :type timeData: Iterable[float]
            :param deltaTime: The time between this current time step and the last one.
            :type deltaTime: float
            :param currentCycleMeasurementLists: An iterable of measurementLists. One leg may potentially use the measurements of another leg.
            :type currentCycleMeasurementLists: Iterable[IMeasurementLists]
            :return: An iterable of actuating values of one or more actuators (depending on how many are one leg).
            :rtype: Iterable[float]
        """
        pass
    
    @abstractmethod
    def exportMeasurementData(self, measurementLists: IMeasurementLists, index: int, isActive: bool) -> dict[str, float | int]:
        """
            A function to format the data of the current RobotABC and related values of the logic controller. Should return a dictionary
            using the names in the NamedTuple that is assigned to this IControlLogic for message passing. A disabled RobotABC
            should return relevant data formatted as NaN to indicate that it is disabled. Data from all RobotABCs are collated together
            into a single NamedTuple.
            
            :param measurementLists: The measurement list that is associated with this RobotABC (and logic controller).
            :type measurementLists: IMeasurementLists
            :param index: The current index of this RobotABC and logic controller (used for discerning the current RobotABC).
            :type index: int
            :param isActive: A flag to determine whether the RobotABC is "active". Should return dictionaries with NaNs if inactive.
            :type isActive: bool
            :return: A dictionary NamedTuple names and their respective values to be used in the datapoint.
            :rtype: dict[str, float | int]
        """
        pass