from functools import partial
import json
from queue import Queue
from typing import Any, Callable

from PySide6 import QtWidgets
from PySide6 import QtCore
from PySide6.QtWidgets import QApplication, QFileDialog, QLabel, QWidget, QMessageBox
from PySide6.QtGui import QColor, QPalette
import logging
from PySide6.QtCore import QObject, QThread, Slot, Signal
import numpy as np
import pandas as pd

from brace.UI.example.GUIController import PrefixNames
from brace.UI.example.PlotConfiguration import ConfiguredStandingPlots
from brace.example.exoskeleton.ControlLogic.ControlLogicDefaults import HardcodedDefaults
from brace.Server.Core.ComInterface import NullCom
from brace.Server.Core.ControlLogic import IControlLogic
from brace.example.exoskeleton.ExoController import ExoController
from brace.example.exoskeleton.ExoLeg import ExoLeg
from brace.example.exoskeleton.ExoMeasurementList import MeasurementLists
from brace.example.exoskeleton.SlewSafetyChecks import SlewSafetyChecks
from brace.example.exoskeleton.ControlLogicLookup import ControlLogicEnum
from brace.RealTimeGraphing.Graphing.AnimatedGraphManager import AnimatedGraphManager, RealTimeType
from brace.RealTimeGraphing.Graphing.DataStream import DataStream
from brace.UI.GUIController import PlotHelpers
from brace.UI.GUIController.UIConfigurationHelpers import hideItem, saveConfiguration
from brace.UI.GraphContext import GraphContext
from brace.UI.example.PlotConfiguration import ConfiguredProportionalPlots
from brace.UI.example.PlotConfiguration import ConfiguredWalkPlots
from brace.UI.example.PlotView import PlotDataTypeHandler
from brace.UI.PlotView.PlotViewer import PlotWindow

from brace.UI.view.ui.Ui_Simulator import Ui_Simulator
import brace.UI.GUIController.InitializationFunctions as InitFunc
import brace.example.exoskeleton.ControlLogic.FSM as FSM5
import brace.example.exoskeleton.ControlLogic.ProportionalControlLogic as Proportional
import brace.example.exoskeleton.ControlLogic.Standing as Standing

logger = logging.getLogger("logger")

def matchEnumToDatatype(dataTypeHandler: PlotDataTypeHandler.IDataTypeHandler):
    return ControlLogicEnum[str(dataTypeHandler.DataType.__name__).upper()]

class Parameters:
    # Leave in hardcoded defaults.
    fsmL = { "forceHysteresisTime" : HardcodedDefaults.forceHysteresisTime, #s change to 0.05? 0.1?
             "velocityHysteresisTime" : HardcodedDefaults.velocityHysteresisTime } #s
    
    fsmR = { "forceHysteresisTime" : HardcodedDefaults.forceHysteresisTime, #s change to 0.05? 0.1?
             "velocityHysteresisTime" : HardcodedDefaults.velocityHysteresisTime} #s
    
    proportionalL = {}

    proportionalR = {}

    standingL = {}

    standingR = {}

def configControlLogics() -> dict[ControlLogicEnum, IControlLogic]:
    fsmControlLogic = lambda index: FSM5.FSMControlLogic(**Parameters.fsmL, index = index) if index == 0 else \
                                         FSM5.FSMControlLogic(**Parameters.fsmR, index = index)
    proportionalControlLogic = lambda index: Proportional.ProportionalControlLogic(**Parameters.proportionalL, index = index) if index == 0 else \
                                            Proportional.ProportionalControlLogic(**Parameters.proportionalR, index = index)
    standingControlLogic = lambda index: Standing.StandingControlLogic(**Parameters.standingL, index = index) if index == 0 else \
                                                Standing.StandingControlLogic(**Parameters.standingR, index = index)
    return { ControlLogicEnum.FSM5: fsmControlLogic,
                ControlLogicEnum.PROPORTIONAL: proportionalControlLogic,
            ControlLogicEnum.STANDING: standingControlLogic}

def extractConfigurationFromSimulationValues() -> dict[str, float]:
    walkKeywords = ConfiguredWalkPlots.WalkPlotsPyQt.velocityKeywordsLR + ConfiguredWalkPlots.WalkPlotsPyQt.thresholdKeywordsLR
    standingKeywords = ConfiguredStandingPlots.StandingPlotsPyQt.kneeAngleThresholdKeywordsLR
    
    return {
        FSM5.FSM5: {keyword: Parameters.fsmL[keyword[0:-1]] if keyword[-1] == 'L' else Parameters.fsmR[keyword[0:-1]] for keyword in walkKeywords},
        Standing.Standing: {keyword: Parameters.standingL[keyword[0:-1]] if keyword[-1] == 'L' else Parameters.standingR[keyword[0:-1]] for keyword in standingKeywords}
    }

class SimulatorWorker(QObject):
    finished = Signal()
    progress = Signal(int)

    def simulateData(self, inputData: pd.DataFrame, apiEvents: pd.DataFrame, multiprocessingQueue: Queue, animatedGraphManagerNew: AnimatedGraphManager) -> None:
        leftCom = np.array([NullCom()])
        rightCom = np.array([NullCom()])

        leftMeasurementList = MeasurementLists()
        rightMeasurementList = MeasurementLists()

        leftSafetyCheck = SlewSafetyChecks(extTorquePositive = True, 
                                        MAX_SLEW_RATE = 80, #nm/s
                                        MAX_EXT_TORQUE = 13, #nm
                                        MAX_FLEX_TORQUE = -13) #nm
        
        rightSafetyCheck = SlewSafetyChecks(extTorquePositive = True, 
                                        MAX_SLEW_RATE = 80, #nm/s
                                        MAX_EXT_TORQUE = 13, #nm
                                        MAX_FLEX_TORQUE = -13) #nm

        exoController = ExoController(initialControlLogicType = ControlLogicEnum.FSM5,
                                    numRobots = 2, 
                                    controlLogic = configControlLogics(),
                                    UPDATE_RATE_PER_SECOND = 500,
                                    robotImplementation = ExoLeg,
                                    simulated = True)
        
        exoController.setInputComInterface(np.array([leftCom, rightCom]))
        exoController.setOutputComInterface(np.array([leftCom, rightCom]))
        exoController.setMeasurementLists(np.array([leftMeasurementList, rightMeasurementList]))
        exoController.setSafetyControl(np.array([leftSafetyCheck, rightSafetyCheck]))

        outputData = exoController.simulateControllerData(measurementDataFrames = inputData, eventPipeLine = apiEvents)
        for data in outputData:
            multiprocessingQueue.put(data)
        animatedGraphManagerNew.noAnimation()
        animatedGraphManagerNew.drawFinalGraph()
        self.finished.emit()

class Simulator(Ui_Simulator, QtWidgets.QMainWindow):
    """
        The GUI window that graphs the saved data fields and reruns the inputs against changed
        configuration loaded parameters. This may be useful in optimizing parameters of a user
        given some zero-mode actuation, or simply attempting to verify the control logic. 
    """

    OUTPUT_FIELDS = ['state', 'torqueDes', 'torqueIn', 'subcontroller']
    def linkPages(self) -> None:
        """
            Forces the two pages of the configuration boxes to change appropriately when a tag is clicked.

            :return: None
            :rtype: None
        """
        oldPages = {objectName: configurationObject for objectName, configurationObject in self.configurationGridOld.__dict__.items() 
                 if isinstance(configurationObject, QtWidgets.QTabWidget)}
        newPages = {objectName: configurationObject for objectName, configurationObject in self.configurationGridNew.__dict__.items() 
                 if isinstance(configurationObject, QtWidgets.QTabWidget)}

        # Hide the pages on the tabs, only can control using the new pages which syncs them.
        for objectName, configurationObject in oldPages.items():
            configurationObject.tabBar().hide()

        for objectName, configurationObject in newPages.items():
            oldObject = oldPages[objectName]
            configurationObject.currentChanged.connect(oldObject.setCurrentIndex)

    @staticmethod
    def isChangedValue(newConfigurationObject: QtWidgets.QWidget, oldConfigurationObject: QtWidgets.QWidget, comparableFunction: Callable, _: Any):
        """
            Changes the field to yellow if the value is different from the new configuration box to the old configuration box.

            :param newConfigurationObject: Widget to be checked and changed to yellow.
            :type newConfigurationObject: QtWidgets.QWidget
            :param oldConfigurationObject: Widget to be checked against.
            :type oldConfigurationObject: QtWidgets.QWidget
            :param comparableFunction: A function that returns some kind of metric of the QWidget, to be compared for equality with between the
            two widgets.
            :type comparableFunction: Callable
            
            :return: None
            :rtype: None
        """
        palette = newConfigurationObject.palette()
        if comparableFunction(newConfigurationObject) != comparableFunction(oldConfigurationObject): # Yellow background
            color = QColor("yellow")
        else:
            color = palette.color(QPalette.ColorRole.Base) # Revert back to original color
        
        palette.setColor(newConfigurationObject.backgroundRole(), color)
        newConfigurationObject.setPalette(palette)
        newConfigurationObject.setAutoFillBackground(True)

    def checkChangedConfiguration(self) -> None:
        """
            Checks the changed configuration every time there is a change in any of the objects
            to determine whether the field should be colored yellow to indicate that there was a change
            made in that field.

            :return: None
            :rtype: None
        """
        for objectName, configurationObject in self.configurationObjectsNew.items():
            match configurationObject:
                case QtWidgets.QSpinBox():
                    configurationObject.valueChanged.connect(partial(Simulator.isChangedValue, configurationObject, self.configurationObjectsOld[objectName], 
                                                                                       QtWidgets.QSpinBox.value))
                case QtWidgets.QDoubleSpinBox():
                    configurationObject.valueChanged.connect(partial(Simulator.isChangedValue, configurationObject, self.configurationObjectsOld[objectName], 
                                                                                       QtWidgets.QDoubleSpinBox.value))
                case QtWidgets.QComboBox():
                    configurationObject.currentIndexChanged.connect(partial(Simulator.isChangedValue, configurationObject, self.configurationObjectsOld[objectName], 
                                                                                       QtWidgets.QComboBox.currentIndex))
                case _:
                    pass

    # TODO: At some point, might be good to change the structure to hierarchical instead of flat symbolics.
    def __init__(self, app: QApplication, initFileConfiguration: dict[str, str | float | int], *args, **kwargs):
        """
            Sets up the application for the Simulator GUI.

            :param app: The QT application that this should be set up against.
            :type app: QApplication
            :param initFileConfiguration: The initialization configuration from the .ini file formatted as a dictionary.
            :type initFileConfiguration: dict[str, Any]
        """
        super().__init__(*args, **kwargs)
        self.app = app
        screenRect = self.app.primaryScreen().geometry()
        self.move(screenRect.top(), screenRect.left())
        self.setupUi(self)

        self.originalTitle = self.windowTitle()
        self.configDictionary = {} # If nothing is loaded, then resetting configuration does nothing.

        # Introspection on own instance variables.
        # Assumptions are that the widgets in the configuration end in "L" or "R"; otherwise should only have single field.
        self.configurationObjectsOld: dict[str, QWidget] = InitFunc.setConfigurationDictionaries(PrefixNames.configurationWidgetNamePrefixes, self.configurationGridOld.__dict__)
        self.configurationObjectsOld.update(InitFunc.setSingleConfigurationDictionaries(PrefixNames.configurationSingleWidgetNamePrefixes, self.configurationGridOld.__dict__))
        for configurationObject in self.configurationObjectsOld.values():
            configurationObject.setDisabled(True)

        self.configurationObjectsNew: dict[str, QWidget] = InitFunc.setConfigurationDictionaries(PrefixNames.configurationWidgetNamePrefixes, self.configurationGridNew.__dict__)
        self.configurationObjectsNew.update(InitFunc.setSingleConfigurationDictionaries(PrefixNames.configurationSingleWidgetNamePrefixes, self.configurationGridNew.__dict__))
        self.configurationLabelsOld: dict[str, QLabel] = InitFunc.setConfigurationDictionaries(PrefixNames.configurationNameLabelPrefixes, self.configurationGridOld.__dict__)
        self.configurationLabelsNew: dict[str, QLabel] = InitFunc.setConfigurationDictionaries(PrefixNames.configurationNameLabelPrefixes, self.configurationGridNew.__dict__)

        # Initializing configuration values based on the ini file.
        self.initFileConfiguration = initFileConfiguration
        initFileDefaults: dict[str, float] = InitFunc.getDefaultsDictionary(self.initFileConfiguration)
        InitFunc.initializeLimits(self.initFileConfiguration.get('limits', {}), self.configurationObjectsOld)
        InitFunc.initializeDefaultParameters(initFileDefaults, self.configurationObjectsOld)
        InitFunc.initializeLimits(self.initFileConfiguration.get('limits', {}), self.configurationObjectsNew)
        InitFunc.initializeDefaultParameters(initFileDefaults, self.configurationObjectsNew)

        # Synchronizing Pages and checking for changed configuration
        self.linkPages()
        self.checkChangedConfiguration()

        # Graphing Items
        self.graphContexts: list[GraphContext] = []
        self.currentContextIndex = 0
        self.MAX_TIME_RANGE = 10

        self.walkGraphContextIndex = ConfiguredWalkPlots.WalkPlotsPyQt.createGraphContext(self.graphContexts, self.plotsPage.walkFSM5GraphToggleHorizontalLayout, 
                                         self.plotsPage.walkFSM5GraphWidget, self.MAX_TIME_RANGE, initFileDefaults, simulator = True)

        self.proportionalGraphContextIndex = ConfiguredProportionalPlots.ProportionalPlotsPyQt.createGraphContext(self.graphContexts, self.plotsPage.proportionalGraphToggleHorizontalLayout, 
                                                               self.plotsPage.proportionalGraphWidget, self.MAX_TIME_RANGE, initFileDefaults, simulator = True)

        self.standingGraphContextIndex = ConfiguredStandingPlots.StandingPlotsPyQt.createGraphContext(self.graphContexts, self.plotsPage.standingGraphToggleHorizontalLayout,
                                                                     self.plotsPage.standingGraphWidget, self.MAX_TIME_RANGE, initFileDefaults, simulator = True)
        PlotHelpers.createHidingBoxes(self, self.graphContexts)

        # For changing dark/light/mode
        self.colorActionGroup = PlotHelpers.setColorActionGroups(self)
        self.app.paletteChanged.connect(lambda _: PlotHelpers.changePlotBackground(self)) 
        PlotHelpers.changePlotBackground(self)

        # Use this one strictly for the simulated outputs (no inputs)
        self.queue = Queue()
        self.animatedGraphManagerNew = AnimatedGraphManager(realTimeType = RealTimeType.SLIDING_WINDOW, backend = 'pyqtgraph')
        self.animatedGraphManagerNew.setQueue(self.queue)
        fsm5GraphContext = self.graphContexts[self.walkGraphContextIndex]
        self.animatedGraphManagerNew.addNewDatastream(fsm5GraphContext.fig, fsm5GraphContext.axes, FSM5.FSM5, 
                                                                                fsm5GraphContext.simulatorAxisLines[FSM5.FSM5], MAX_TIME_RANGE = self.MAX_TIME_RANGE)
        
        proportionalGraphContext = self.graphContexts[self.proportionalGraphContextIndex]
        self.animatedGraphManagerNew.addNewDatastream(proportionalGraphContext.fig, proportionalGraphContext.axes, Proportional.Proportional, 
                                                                                proportionalGraphContext.simulatorAxisLines[Proportional.Proportional], MAX_TIME_RANGE = self.MAX_TIME_RANGE)
        
        standingGraphContext = self.graphContexts[self.standingGraphContextIndex]
        self.animatedGraphManagerNew.addNewDatastream(standingGraphContext.fig, standingGraphContext.axes, Standing.Standing,
                                                                                standingGraphContext.simulatorAxisLines[Standing.Standing], MAX_TIME_RANGE = self.MAX_TIME_RANGE)

        self.configurationButtons.loadDataFilePushButton.clicked.connect(self.openDataset)
        self.configurationButtons.simulatePushButton.clicked.connect(self.createSimulatorThread)
        self.configurationButtons.resetAllConfigurationPushButton.clicked.connect(self.askSetAllConfirmationFromSaveFile)
        self.configurationButtons.resetCurrentConfigurationPushButton.clicked.connect(self._setCurrentConfigurationFromSaveFile)
        self.configurationButtons.saveCurrentConfigurationPushButton.clicked.connect(lambda: saveConfiguration(self, self.configurationObjectsNew))

        self.configurationButtons.toggleConfigurationButtons(enable = False)

        self.leftActive = False
        self.rightActive = False
                        
        # Separate thread for dealing with simulation code.
        self.simulatorThread = QThread()
        self.simulatorWorker = SimulatorWorker()

        self.dataStreams: list[DataStream] = [] # Saved for deleting data afterwards such that old data does not persist despite new data.

    def openDataset(self) -> None:
        """
            Opens the dataset, looking for only parquet files, getting the configuration and then graphing
            them into the plots.

            :return: None
            :rtype: None
        """
        options = QFileDialog.Option() # Must use DontUseNativeDialog for other options to work.
        openDatasetFileDialog = QFileDialog(self)
        fileName, _ = openDatasetFileDialog.getOpenFileName(self, "Load Dataset File", 
                                                           "", "Parquet Files (*.parquet)", options = options)
        self.setWindowTitle(f"{self.originalTitle} - {fileName}")

        # Parse dataset and graph. Only supports parquet for now. 
        if fileName:
            ds = pd.read_parquet(fileName)

            try:
                self.listOfDatatypes = ds.columns.to_list()
                if 'Configuration' in self.listOfDatatypes:
                    self.listOfDatatypes.remove('Configuration')
                    self.configDictionary = ds['Configuration'][0]

                apiEvents = pd.DataFrame()
                if 'APIEvents' in self.listOfDatatypes:
                    self.listOfDatatypes.remove("APIEvents")
                    apiEvents = PlotWindow.parseParquetString(ds, 'APIEvents')

                # Sets both the old and new to the values set in the save file.
                self._setAllConfigurationFromSaveFile()
                self._graphOldData(ds)
                self.inputData, self.apiEvents = self._formatDataForSimulation(ds, apiEvents) # These should remain static until another set is used.
                self.configurationButtons.toggleConfigurationButtons(enable = True)
            except ValueError as e:
                logger.error(e)
    
    def _graphOldData(self, ds: pd.DataFrame) -> None:
        """
            Graphs the old data from a pandas Dataframe into the relevant plot, clearing out any old lines
            that were on the simulator.

            :params ds: Dataframe containing data from the NamedTuple.
            :type ds: pandas.DataFrame

            :return: None
            :rtype: None
        """
        graphOldDs = ds.copy() # Could be bad memory-wise.

        # Clear data and then remove
        for datastream in self.dataStreams:
            datastream.clearData()
            
        self.dataStreams.clear()
        self.animatedGraphManagerNew.reset() # Then clear out simulator lines.
        for datatypeName in self.listOfDatatypes:
            graphContextToUse = None
            indexToUse = None
            dataTypeHandler = PlotDataTypeHandler.getDataTypeHandler(datatypeName)
            for i, graphContext in enumerate(self.graphContexts):
                if graphContext.dataType == dataTypeHandler.DataType:
                    graphContextToUse = graphContext
                    indexToUse = i
                    break
            if graphContextToUse is not None:
                self.plotsPage.plotTabWidget.setCurrentIndex(indexToUse) # Workaround for the final draw not setting the right time length
                self.leftActive, self.rightActive, datastream = Simulator.graphLegDataParquet(graphContextToUse, graphContext.dataType, graphOldDs)
                self.dataStreams.append(datastream)
            
            self.toggleLegConfigurationVisibility()

    def isLeftLegActive(self) -> bool:
        return self.leftActive
    
    def isRightLegActive(self) -> bool:
        return self.rightActive
    
    def toggleLegConfigurationVisibility(self) -> None:
        """
            Disables the visibility of the leg configuration if the leg was not active in that particular
            streamed sesssion.

            :return: None
            :rtype: None        
        """
        hideLeftLegConfiguration = not self.isLeftLegActive()
        hideRightLegConfiguration = not self.isRightLegActive()

        legWidgetOld = { **self.configurationObjectsOld, **self.configurationLabelsOld }
        legWidgetNew = { **self.configurationObjectsNew, **self.configurationLabelsNew }
        for configurationWidgetName, configurationWidgetObject in legWidgetOld.items():
            hideItem(configurationWidgetName, configurationWidgetObject, hideLeftLegConfiguration, hideRightLegConfiguration)
        
        for configurationWidgetName, configurationWidgetObject in legWidgetNew.items():
            hideItem(configurationWidgetName, configurationWidgetObject, hideLeftLegConfiguration, hideRightLegConfiguration)

        # Update the contexts so that they are visible on turn on.
        for contexts in self.graphContexts:
            contexts.fig.toggleLeftLegs(not hideLeftLegConfiguration)
            contexts.fig.toggleRightLegs(not hideRightLegConfiguration)
    
    def _formatDataForSimulation(self, ds: pd.DataFrame, apiEvents: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
        """
            Formats the data into a pandas dataframe for running as simulator data, removing some of the
            unnecessary columns.
            This initializes it to the right controller (whichever is initialized at the beginning) since there
            is no corresponding event that changes this control logic. Returns the pandas dataframes formatted for the simulator.

            :param ds: Pandas Dataframe containing the data
            :type ds: pandas.DataFrame
            :param apiEvents: Pandas Dataframe containing the RPC events.
            :type apiEvents: pandas.DataFrame

            :return: Formatted pandas dataframes for the data and the API calls.
            :rtype: tuple[pandas.DataFrame, pandas.DataFrame]
        """
        simulatorDs = ds.copy()
        leftDataFrame = pd.DataFrame({})
        rightDataFrame = pd.DataFrame({})
        for datatypeName in self.listOfDatatypes:
            dataTypeHandler = PlotDataTypeHandler.getDataTypeHandler(datatypeName)                   
            if dataTypeHandler is not None:
                if PlotWindow.checkParquetIndex(simulatorDs, dataTypeHandler.DataType, 'L'):
                    leftLeg: pd.DataFrame = PlotWindow.parseParquet2(simulatorDs, dataTypeHandler.DataType, 'L')
                    leftLeg = leftLeg.drop(columns = Simulator.OUTPUT_FIELDS, errors = 'ignore')
                    leftLeg['_controllerType'] = matchEnumToDatatype(dataTypeHandler)
                    leftDataFrame = pd.concat([leftDataFrame, leftLeg])
                    
                if PlotWindow.checkParquetIndex(simulatorDs, dataTypeHandler.DataType, 'R'): 
                    rightLeg = PlotWindow.parseParquet2(simulatorDs, dataTypeHandler.DataType, 'R')
                    rightLeg['_controllerType'] = matchEnumToDatatype(dataTypeHandler)
                    rightLeg = rightLeg.drop(columns = Simulator.OUTPUT_FIELDS, errors = 'ignore')
                    rightDataFrame = pd.concat([rightDataFrame, rightLeg])

            inputData = [dataframe.sort_values(by = 'uptime') if not dataframe.empty else dataframe for dataframe in [leftDataFrame, rightDataFrame]]

            # Add turned on controllers for the session.
            startingControllers = []
            addedStartingController = False
            for j in range(len(inputData)):
                activeLeg = json.dumps({'index': j, 'enable': not inputData[j].empty})
                startingControllers.append({'uptime': 0.0, 'functionName': 'turnOnOffControllerRobot','functionParameters': activeLeg})
                
                # Add the logic controller only on the first instance; no repeats.
                if not addedStartingController and not inputData[j].empty:
                    activeStartingController = json.dumps({'controlLogicType': int(inputData[j]['_controllerType'].iat[0])})
                    startingControllers.append({'uptime': 0.0, 'functionName': 'changeControlLogic', 'functionParameters': activeStartingController})
                    addedStartingController = True
                inputData[j].drop(['_controllerType'], errors = 'ignore')
        
            startingControllers = pd.DataFrame(startingControllers)
            apiEvents: pd.DataFrame = pd.concat([apiEvents, startingControllers], ignore_index = True)
            inputData = inputData
            apiEvents = apiEvents.sort_values(by = 'uptime', ignore_index = True)
        return inputData, apiEvents
    
    @Slot()
    def askSetAllConfirmationFromSaveFile(self) -> None:
        """
            Confirmation box to reset all of the configuration values back to the original values.

            :return: None
            :rtype: None
        """
        """ Ask confirmation box for resetting all of the simulation configuration """
        confirmation = QMessageBox.question(self, 'Confirmation Reset All', 
                                     'Reset all simulation configuration (values will be lost)?', 
                                     QMessageBox.Yes | QMessageBox.No)
        
        if confirmation == QMessageBox.StandardButton.Yes:
            self._setAllConfigurationFromSaveFile()

    @Slot()
    def _setAllConfigurationFromSaveFile(self) -> None:
        """
            Sets all of the configuration the configuration file onto both the top (permanent)
            and bottom (configurable) configuration boxes in the simulator.

            :return: None
            :rtype: None
        """
        for controllerName, controllerLegs in self.configDictionary.items():
            dataTypeHandler = PlotDataTypeHandler.getDataTypeHandler(controllerName)
            for graphContext in self.graphContexts:
                if graphContext.dataType == dataTypeHandler.DataType:
                    graphContextToUse = graphContext
                    break

            if (leftControllerLeg := controllerLegs['L']) is not None:
                graphContextToUse.readConfigurationFromSaveFileFunc(self.configurationObjectsOld, leftControllerLeg, True)
                graphContextToUse.readConfigurationFromSaveFileFunc(self.configurationObjectsNew, leftControllerLeg, True)
            
            if (rightControllerLeg := controllerLegs['R']) is not None:
                graphContextToUse.readConfigurationFromSaveFileFunc(self.configurationObjectsOld, rightControllerLeg, False)
                graphContextToUse.readConfigurationFromSaveFileFunc(self.configurationObjectsNew, rightControllerLeg, False)

    @Slot()
    def _setCurrentConfigurationFromSaveFile(self) -> None:
        """
            Sets the configuration from the save file onto the simulator plots, calling the appropriate
            function from the GraphContext.

            :return: None
            :rtype: None
        """
        currentController = self.configurationGridNew.configurationTabs.currentIndex()
        currentGraphContext = self.graphContexts[currentController]

        controllerLegs = self.configDictionary.get(currentGraphContext.dataType.__name__)
        if controllerLegs:
            if (leftControllerLeg := controllerLegs['L']) is not None:
                currentGraphContext.readConfigurationFromSaveFileFunc(self.configurationObjectsOld, leftControllerLeg, True)
                currentGraphContext.readConfigurationFromSaveFileFunc(self.configurationObjectsNew, leftControllerLeg, True)
            
            if (rightControllerLeg := controllerLegs['R']) is not None:
                currentGraphContext.readConfigurationFromSaveFileFunc(self.configurationObjectsOld, rightControllerLeg, False)
                currentGraphContext.readConfigurationFromSaveFileFunc(self.configurationObjectsNew, rightControllerLeg, False)

    def createSimulatorThread(self) -> None:
        """
            Creates a separate thread running the simulator, allowing the user to continue running the GUI as desired.

            :return: None
            :rtype: None
        """
        # Initialize configuration things first.
        leftConfiguration, rightConfiguration = {}, {}
        passedChecks = True
        for graphContext in self.graphContexts:
            leftConfiguration, rightConfiguration = graphContext.getConfigurationChangesFunc(self.configurationObjectsNew, 
                                                     self.configurationGridNew)
            
            # Exit out for invalid configuration
            # TODO: Need to figure out where to show where validation failed.
            passedChecks = passedChecks and (graphContext.validateConfigurationFunc(self.configurationGridNew, self.isLeftLegActive(), 
                                                                                    True, leftConfiguration) \
                and graphContext.validateConfigurationFunc(self.configurationGridNew, self.isRightLegActive(),
                                                            False, rightConfiguration))

            # Left and Right configuration management.
            match graphContext.controlLogicType:
                case ControlLogicEnum.FSM5:
                    left, right = Parameters.fsmL, Parameters.fsmR
                case ControlLogicEnum.PROPORTIONAL:
                    left, right = Parameters.proportionalL, Parameters.proportionalR
                case ControlLogicEnum.STANDING:
                    left, right = Parameters.standingL, Parameters.standingR
            left.update(leftConfiguration)
            right.update(rightConfiguration)

        # Do not continue if failed checks.
        if not passedChecks:
            return
        else:
            for graphContext in self.graphContexts:
                leftConfiguration, rightConfiguration = graphContext.getConfigurationChangesFunc(self.configurationObjectsNew, 
                                                        self.configurationGridNew)
                graphContext.adjustPlotThresholdValuesFunc(self, leftConfiguration, rightConfiguration)

        self.simulatorThread = QThread()
        self.simulatorWorker = SimulatorWorker() # Create new thread worker and move ownership
        self.simulatorWorker.moveToThread(self.simulatorThread)

        # Start events for connection and finished.
        self.simulatorThread.started.connect(lambda: self.simulatorWorker.simulateData(self.inputData, self.apiEvents, self.queue, self.animatedGraphManagerNew))
        self.simulatorWorker.finished.connect(self.simulatorThread.quit)
        self.simulatorWorker.finished.connect(self.simulatorWorker.deleteLater)
        self.simulatorThread.finished.connect(self.simulatorThread.deleteLater)
        
        # Change cursor and configuration button widget state, popping when finished.
        self.simulatorThread.start()
        QApplication.setOverrideCursor(QtCore.Qt.CursorShape.WaitCursor)
        self.configurationButtons.setEnabled(False)
        self.simulatorThread.finished.connect(lambda: self.configurationButtons.setEnabled(True))
        self.simulatorThread.finished.connect(QApplication.restoreOverrideCursor)

    @staticmethod
    def graphLegDataParquet(graphContext: GraphContext, dataType: type, ds: pd.DataFrame) -> tuple[bool, bool, DataStream]:
        """
            Graphs the parquet file data (in similar fashion to the open file method). Datastreams are updated
            and are intended to be constant unlike the simulator values which may be changed.

            :param graphContext: The graph context that should be used for graphing.
            :type graphContext: GraphContext
            :param dataType: The NamedTuple datatype that should be graphed.
            :type dataType: type
            :param ds: The data stream that is to be graphed onto the corresponding graphs.
            :type ds: pandas.DataFrame

            :return: Tuple containing whether the left leg, right leg are active; and the datastream containing the data.
            :rtype: tuple[bool, bool, DataStream]
        """
        leftActive, rightActive = False, False
        datastream = DataStream(graphContext.fig, graphContext.axes.flat, graphContext.axisLines[dataType], dataType, backend = 'pyqtgraph')

        if leftActive := PlotWindow.checkParquetIndex(ds, dataType, 'L'):
            _, uptime, leftLeg = PlotWindow.parseParquet(ds, dataType, 'L')
            for name, values in leftLeg.items():
                datastream.updatePoints(name, uptime, values) # Some lines are not drawn, but are included in the dataset.  
        
        if rightActive := PlotWindow.checkParquetIndex(ds, dataType, 'R'):
            _, uptime, rightLeg = PlotWindow.parseParquet(ds, dataType, 'R')
            for name, values in rightLeg.items():
                datastream.updatePoints(name, uptime, values) # Some lines are not drawn, but are included in the dataset.
        datastream.updateTime(uptime)
        datastream.drawFinal(padding = 0.05)
        return leftActive, rightActive, datastream