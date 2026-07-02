from collections import deque
from typing import NamedTuple, override
from brace.example.exoskeleton.ExoMeasurementList import MeasurementLists
from brace.Server.Core.ControlLogic import IControlLogic
import numpy as np

class Proportional(NamedTuple):
    """
        NamedTuple that holds information for this control iteration.
        All NamedTuples should have at the minimum "t" for time.
        L and R are suffixed at the end for left and right data values.
        All values that are used in the IControlLogic class should be included
        such that it may be replicated in simulation.

        For the Proportional NamedTuple, many more inputs are given than required
        for execution in the simulator, however it may still be useful to keep these
        input values for future use.
    """
    thetaL: float
    thetaR: float
    thetaDotWinL: float
    thetaDotWinR: float
    fsrL: float
    fsrR: float
    torqueInL: float
    torqueInR: float
    t: float #time vector

class ProportionalControlLogic(IControlLogic):
    """
        This control logic is simple, creates a proportional torque response
        with respect to the knee angle of the exoskeleton. Negative torque pushes the user
        to extension, tapering torque as it reaches full extension, while positive torque would
        lock the user into flexion.
    """
    DataClass = Proportional

    def __init__(self, index: int, thetaMin: int, thetaMax: int, minTorque: float, maxTorque: float):
        """
            :param index: The index of the leg with respect to the RobotAssemblyABC.
            :type index: int
            :param thetaMin: The minimum knee angle that is allowed for this control logic before cutoff.
            :type thetaMin: int
            :param thetaMax: The maxmimum knee angle that is allowed for this control logic before cutoff.
            :type thetaMax: int
            :param minTorque: The minimum torque value (negative values indicate extension). 
            :type minTorque: float
            :param maxTorque: The maximum torque value (positive values indicate flexion).
            :type maxTorque: float
        """
        super().__init__(index)
        self.thetaMin = thetaMin
        self.thetaMax = thetaMax
        self.minTorque = minTorque
        self.maxTorque = maxTorque

    @override
    def setup(self, **kwargs) -> None:
        """
            No necessary setup is needed for proportional response.
            
            :param kwargs: Keywoard arguments
            :type kwargs: dict[str, Any]
            :return: None
            :rtype: None
        """
        pass

    @override
    def simulatedSetup(self, **kwargs) -> None:
        """
            No necessary setup is needed for simulated proportional response.
            
            :param kwargs: Keywoard arguments
            :type kwargs: dict[str, Any]
            :return: None
            :rtype: None
        """
        pass

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
        for parameterName, parameterValues in parameters.items():
            self.__setattr__(parameterName, parameterValues)

    @override
    def getConfigurationParameters(self, formatForConfiguration: bool) -> dict[str, float | dict]:
        """
            Returns the configuration parameters to be used in updating the GUI or retrieved
            for saving into the save files. Since there are no states that need to be imported
            formatting the configuration for enum string names is not required.
            
            :param formatForConfiguration: Set to True if saving for a save file.
            :type formatForConfiguration: bool
            :return: The parameter configuration for the control law.
            :rtype: dict[str, float | dict]
        """
        controllerParameters = {
            "thetaMin": self.thetaMin, # deg
            "thetaMax": self.thetaMax, # deg
            "minTorque": self.minTorque, # Nm
            "maxTorque": self.maxTorque # Nm
        }
        return controllerParameters

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
        TorqueDes = 0.0
        if enable:
            measurementLists: MeasurementLists = self.getRespectiveMeasurementList(currentCycleMeasurementLists)
            theta = measurementLists.angleMesAll[-1]
            if theta <= self.thetaMin:
                TorqueDes = self.maxTorque
            elif theta >= self.thetaMax:
                TorqueDes = self.minTorque
            else:
                # Calculate the proportional torque within the bounds (Flexion is positive, extension is negative).
                TorqueDes = self.maxTorque - (self.maxTorque - self.minTorque) * (theta - self.thetaMin) / (self.thetaMax - self.thetaMin)
        return [TorqueDes]
    
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
            'thetaDotWin':measurementLists.windowedAngularVelocityAll[-1] if isActive else np.nan,
            "fsr": measurementLists.forceMesAll[-1] if isActive else np.nan,
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