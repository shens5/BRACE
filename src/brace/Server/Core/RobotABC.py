from collections.abc import Iterable
from enum import IntEnum
from typing import Any, Callable, NamedTuple

import pandas as pd
from brace.Server.Core.ComInterface import IComInterface, IInputCom, IOutputCom, UnexpectedInitializationError
from brace.Server.Core.SafetyControl import ISafetyControl
from brace.Server.Core.MeasurementLists import IMeasurementLists
from brace.Server.Core.ControlLogic import IControlLogic
import logging
logger = logging.getLogger("logger")

class RobotABC():
    """ 
    A functional robotic set of input and output communications interfaces and safety control layers that
    behave under a set of control logic classes.
    """

    def __init__(self, controlLogic: dict[IntEnum, Callable[[int], IControlLogic]],
                 debugMode: bool, index: int, initialControlLogicType: IntEnum):
        """
        :params controlLogic: A dictionary of IntEnums as the keys and a generator that creates control logic classes
        as a value, taking the index as a parameter.
        :type controlLogic: dict[IntEnum, Callable[[int], IControlLogic]]
        :params debugMode: A boolean that refers to whether or not actuation should be started at the beginning.
        :type debugMode: bool
        :params index: Index of the RobotABC with respect to its position in RobotAssemblyABC.
        :type index: int
        :params initialControlLogicType: The initialized control logic type at the beginning of creation. This should be an IntEnum
        based on what is available in the controlLogic dictionary.
        :type initialControlLogicType: IntEnum
        """
        self.measurementLists: IMeasurementLists = None 

        #if true, sends zero torque to exo
        self.debugMode = debugMode
        self.index = index
        self.controlLogic = {controlLogic: controlLogicFunc(self.index) for controlLogic, controlLogicFunc in controlLogic.items()}
        self.currentControlLogic = self.controlLogic[initialControlLogicType]
        
        self.enable = False
        self.inputComs: Iterable[IInputCom] = []
        self.outputComs: Iterable[IOutputCom] = []
        self.safetyControl: ISafetyControl = None

    def addInputComs(self, inputComs: Iterable[IInputCom]) -> None:
        """ 
            Add the input communications adapters. The ordering should be preserved, and thus should be used to distinguish interfaces. 

            :params inputComs: A list of IInputCom objects that will be used in reading in sensor information.
            :type inputComs: Iterable[IInputCom]
            :return: None
            :rtype: None
        """
        self.inputComs = inputComs

    def addOutputComs(self, outputComs: Iterable[IOutputCom]) -> None:
        """ 
            Add the output communications adapters. The ordering is preserved, and thus should be used to 
            enumerate with the data bytes for actuation.

            :params outputComs: A list of IOutputCom objects that will be used in actuation.
            :type outputComs: Iterable[IOutputComs]
            :return: None
            :rtype: None
        """
        self.outputComs = outputComs

    def addMeasurementList(self, measurementList: IMeasurementLists) -> None:
        """ 
            Add the measurement list as way of storing the data to be used in the logic controllers.

            :params measurementList: The IMeasurementList object that should be used to store this RobotABCs data.
            :type measurementList: IMeasurementLists
            :return: None
            :rtype: None
        """
        self.measurementLists = measurementList

    def addSafetyControls(self, safetyControls: ISafetyControl) -> None:
        """ Add safety control object to the RobotABC instance.

            :params safetyControls: The ISafetyControl object to be used on this RobotABC to constrain outputs and convert.
            :type safetyControls: ISafetyControls
            :return: None
            :rtype: None
        """
        self.safetyControl = safetyControls

    # Things that should be initialized after constructor. 
    def setup(self, **kwargs: dict[str, Any]) -> None:
        """
            Executes to initialize after the constructor, but just before the control iteration starts (transient state). 
            Initializes the IMeasurementList.
            
            :params kwargs: Keyword arguments passed to controlLogic.
            :type kwargs: dict[str, Any]
            :return: None
            :rtype: None
        """

        for controlLogic in self.controlLogic.values():
            controlLogic.setup(**kwargs)

        self.measurementLists.setupMeasurements(self.inputComs)

    # Things that should be initialized after constructor. This runs the transient state.
    def simulatedSetup(self, **kwargs) -> None:
        """
            Executes to initialize after the constructor, but just before the control iteration starts (transient state). 
            Initializes the IMeasurementList. Specifically running the simulated setups of each.
            
            :params kwargs: Keyword arguments passed to controlLogic simulated setup.
            :type kwargs: dict[str, Any]
            :return: None
            :rtype: None
        """
        for controlLogic in self.controlLogic.values():
            controlLogic.simulatedSetup(**kwargs)
        self.measurementLists.simulateSetupMeasurements()
    
    def changeControlLogic(self, controlLogicType: IntEnum) -> None:
        """
            Changes the current control logic object based on the corresponding IntEnum from the controlLogicType.

            :params controlLogicType: The IntEnum in controlLogic dictionary that should be changed to.
            :type controlLogicType: IntEnum
            :return: None
            :rtype: None 
        """
        self.currentControlLogic = self.controlLogic[controlLogicType]

    def changeControlLogicParameters(self, controlLogicType: IntEnum, parameters: dict[str, float | dict[str, float]]) -> None:
        """
            Calls the control logic object to change the parameters.

            :params controlLogicType: The IntEnum of the control logic class that should have their parameters changed.
            :type controlLogicType: IntEnum
            :params parameters: Dictionary of keywords and values to change the control logic parameters.
            :type parameters: dict[str, float | dict[str, float]]
            :return: None
            :rtype: None
        """
        self.controlLogic[controlLogicType].setParameters(parameters = parameters)

    def enableActuation(self, enable: bool) -> None:
        """
            Enables the actuation based on a boolean flag. Actuation values will still be calculated, but not performed.

            :params enable: Whether or not actuation should be enabled.
            :type enable: bool
            :return: None
            :rtype: None
        """
        self.debugMode = not enable # Enabled torque == not debug mode.

    def setCalibrationOffset(self) -> None:
        """
            Calls the IMeasurementLists to zero calibration offset values.

            :return: None
            :rtype: None
        """
        self.measurementLists.setCalibrationOffset(self.inputComs)

    def getConfigurationParameters(self, controlLogicType: IntEnum, formatForConfiguration: bool) -> dict[str, float | dict]:
        """
            Gets the configuration parameters for a given control logic object. May format it for configuration file needs as necessary.

            :params controlLogicType: The IntEnum for the control logic object that should be received.
            :type controlLogicType: IntEnum
            :params formatForConfiguration: A boolean that indicates whether or not the return configuration should be formatted for the data file configuration
        (e.g. dictionary with strings as keys instead of Enums, to preserve names).
        Should be true if for file (such as exported data trial configuration), false for regular GUI management.
            :type formatForConfiguration: bool

            :return: None
            :rtype: None
        """
        configurationParameters = self.controlLogic[controlLogicType].getConfigurationParameters(formatForConfiguration)
        return configurationParameters
        
    def turnOnOffRobot(self, enable: bool) -> bool:
        """
            Enables the RobotABC. The input and output interfaces are turned off. A failure to turn on the RobotABC
            disables the RobotABC.

            :params enable: Whether or not this RobotABC should be turned on or off.
            :type enable: bool

            :return: Whether or not enabling or disabling this RbbotABC was successful.
            :rtype: bool
        """
        # Disable both input and output coms. In a set prevents duplicates in case of both input and output.
        coms: set[IComInterface] = {*self.inputComs, *self.outputComs}
        try:
            for com in coms:
                com.turnOnOffComm(enable = enable)
            self.enable = enable
            return True
        except UnexpectedInitializationError as e:
            logger.error(f"Failed on turnOnOffRobot: {enable} on {coms}")
            # Attempt to close off all other coms.
            for com in coms:
                com.turnOnOffComm(enable = False)
            self.enable = False
            return False
    
    def runMeasurements(self, deltaTimeAll: Iterable[float]) -> IMeasurementLists:
        """
            Runs the measurement collection for this cycle.

            :params deltaTimeAll: A list of floats that refers to the amount of time between control iterations.
            :type deltaTimeAll: Iterable[float]

            :return The IMeasurementList that was updated.
            :rtype IMeasurementLists
        """
        # Run the measurements on input coms.
        self.measurementLists.runMeasurements(deltaTimeAll = deltaTimeAll, inputComs = self.inputComs)
        return self.measurementLists
    
    def copyMeasurements(self, i: int, measurementDataFrameToCopy: pd.DataFrame) -> IMeasurementLists:
        """
            Copies the measurement data (used in simulation) to this RobotABC's IMeasurementLists.

            :params i: The index of this current control iteration.
            :type i: int
            :params measurementDataFrameToCopy: The pandas Dataframe containing the relevant input data.
            :type measurementDataFrameToCopy: pandas.DataFrame
            
            :return: The IMeasurementLists that was updated.
            :rtype: IMeasurementLists
        
        """
        self.measurementLists.copyMeasurements(i, measurementDataFrameToCopy)
        return self.measurementLists
    
    def runCycle(self, timeAll: Iterable[float], deltaTimeAll: Iterable[float], 
                 currentCycleMeasurementLists: Iterable[IMeasurementLists]) -> None:
        
        """
            Runs the iteration cycle using the current IMeasurementLists and time data.
        
            :params timeAll: A list of times for the beginning of each iteration cycle.
            :type timeAll: Iterable[float]
            :params deltaTimeAll: A list of containing the amount of time in between each iteration cycle.
            :type deltaTimeAll: Iterable[float]
            :params currentCycleMeasurementLists: A list of IMeasurementLists (for each RobotABC for cross RobotABC dependencies)
            that can be used for control.
            :type currentCycleMeasurementLists: Iterable[IMeasurementLists]

            :returns: None
            :rtype: None
        """
        outputDes = self.currentControlLogic.getDesiredOutputValues(self.enable, timeAll, deltaTimeAll[-1], currentCycleMeasurementLists)
        outputInList = self.safetyControl.runSafetyControl(self.measurementLists, deltaTimeAll, outputDes)
        self.measurementLists.recordOutputValues(outputDes, outputInList)
        outputMsgData = self.safetyControl.runOutputConversion(outputInList)

        if not self.debugMode:
            for outputCom, outputMsgData in zip(self.outputComs, outputMsgData):
                outputCom.sendOutput(outputMsgData = outputMsgData)
    
    def exportRobotData(self) -> tuple[NamedTuple, dict[str, float | int]]:
        """
            Exports the data for the current control iteration, getting the assigned DataClass \
                and the dictionary of data given by the control logic for the given control logic object.

            :returns: Tuple of the DataClass (NamedTuple type) and dictionary of relevant information.
            :rtype: tuple[NamedTuple, dict[str, float | int]]        
        """
        controlLogicDataType = self.currentControlLogic.DataClass
        robotData = self.currentControlLogic.exportMeasurementData(measurementLists = self.measurementLists, 
                                                                 index = self.index, isActive = self.enable)
        return controlLogicDataType, robotData