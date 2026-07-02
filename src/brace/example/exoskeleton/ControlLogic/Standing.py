from __future__ import annotations
from collections import deque
from typing import NamedTuple

from brace.example.exoskeleton.ExoMeasurementList import MeasurementLists
from brace.Server.Core.ControlLogic import IControlLogic
import brace.Server.Core.RobotHelpers as RobotHelpers
from typing import override
import numpy as np
import logging
logger = logging.getLogger("logger")

class Standing(NamedTuple):
    """
        NamedTuple that holds information for this control iteration.
        All NamedTuples should have at the minimum "t" for time.
        L and R are suffixed at the end for left and right data values.
        All values that are used in the IControlLogic class should be included
        such that it may be replicated in simulation.

        For the Standing NamedTuple, many more inputs are given than required
        for execution in the simulator, however it may still be useful to keep these
        input values for future use.
    """
    thetaL: float
    thetaR: float
    fsrL: float
    fsrR: float
    thetaDotWinL: float
    thetaDotWinR: float
    torqueDesL: float
    torqueDesR: float
    torqueInL: float
    torqueInR: float
    t: float #time vector

class StandingControlLogic(IControlLogic):
    """
       This logic controller forces the user into extension when a threshold
       angle is met in flexion. The torque is then applied in the extension direction
       which forces them into the turn-off threshold. Traditionally, this is built in
       as a state in other controllers, but this is made as a dedicated standing
       controller.
    """
    DataClass = Standing

    def __init__(self, standingMode: bool, standingTorque: float, slewRate: int, turnOnThreshold: int, turnOffThreshold: int, index: int):
        """
            :params standingMode: Whether standing mode is enabled or disabled (produces the torque in actuated mode).
            :type standingMode: bool
            :params standingTorque: The amount of torque that should be applied when the turn-on angle threshold is met.
            :type standingTorque: float
            :params slewRate: The maximum slope in torque when the torque is applied.
            :type slewRate: int
            :params turnOnThreshold: The knee angle at which this torque should be applied.
            :type turnOnThreshold: int
            :params turnOffThreshold: The knee angle at which torque should be disabled after it is applied.
            :type turnOffThreshold: int
            :param index: The index of the leg with respect to the RobotAssemblyABC.
            :type index: int
        """
        super().__init__(index = index)
        self.standingMode = standingMode
        self.standingTorque = standingTorque
        self.slewRate = slewRate
        self.turnOnThreshold = turnOnThreshold
        self.turnOffThreshold = turnOffThreshold

        self.applyingTorque = False

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
        # forceSensorThresholdInitialContact, forceSensorThresholdSwing
        # deadZoneTime, stateTorques, timeoutTime
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
            "standingMode": self.standingMode, # deg
            "standingTorque": self.standingTorque, # deg
            "slewRate": self.slewRate,
            "turnOnThreshold": self.turnOnThreshold, # Nm
            "turnOffThreshold": self.turnOffThreshold # Nm
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
        measurementLists: MeasurementLists = self.getRespectiveMeasurementList(currentCycleMeasurementLists)
        angleMeasurement = measurementLists.angleMesAll[-1]
        cappedTorqueDes = 0.0
        if enable and self.standingMode:
            if not self.applyingTorque and angleMeasurement >= self.turnOnThreshold:
                self.applyingTorque = True
            elif self.applyingTorque and angleMeasurement <= self.turnOffThreshold:
                self.applyingTorque = False

            torqueDes = self.standingTorque if self.applyingTorque else 0.0
            cappedTorqueDes = RobotHelpers.checkSlewRate(torqueDes, measurementLists.torqueInAll[-1], deltaTime, self.slewRate)
        
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