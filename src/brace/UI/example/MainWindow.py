import pickle
from queue import Queue, Empty
from string import Template
from typing import Any, override
from PySide6.QtCore import QTimer, Slot, Qt, Signal
from PySide6.QtWidgets import QMainWindow, QFileDialog, QWidget, QLabel, QApplication, QComboBox, QAbstractSpinBox
from brace.UI.GUIController.UIConfigurationHelpers import hideItem, saveConfiguration
from brace.UI.GraphContext import GraphContext
from brace.UI.example.Simulator import Simulator
from brace.UI.view.ui.Ui_MainWindow import Ui_MainWindow
from pyqtgraph import GraphicsLayoutWidget
import json
from datetime import datetime
import logging
import time
from brace.UI.SaveDialog import SaveDialog
from brace.UI.LoggingHelpers import redBoldText, TextBrowserHandler
from brace.RealTimeGraphing.Graphing.IDataProducer import IDataProducer
import brace.UI.example.GUIController.PrefixNames as PrefixNames
import brace.UI.GUIController.InitializationFunctions as InitFunc
import brace.UI.example.PlotConfiguration.ConfiguredWalkPlots as ConfiguredWalkPlots 
import brace.UI.example.PlotConfiguration.ConfiguredProportionalPlots as ConfiguredProportionalPlots
import brace.UI.example.PlotConfiguration.ConfiguredStandingPlots as ConfiguredStandingPlots
from brace.UI.PlotView.PlotViewer import PlotWindow
import brace.UI.GUIController.PlotHelpers as PlotHelpers

from paho.mqtt import client as mqtt
from concurrent.futures import ThreadPoolExecutor
import socket

import sys
from brace.RealTimeGraphing.Graphing.AnimatedGraphManager import AnimatedGraphManager, RealTimeType
from brace.example.exoskeleton.ControlLogic.FSM import FSM5
from brace.example.exoskeleton.ControlLogicLookup import ControlLogicEnum
from brace.example.exoskeleton.ControlLogic.ProportionalControlLogic import Proportional
from brace.example.exoskeleton.ControlLogic.Standing import Standing
from brace.Server.GPIOSynch.PushButton import Trigger, ButtonPress

import logging
logger = logging.getLogger("logger")

class MainWindow(QMainWindow, Ui_MainWindow):
    triggerPressSignal = Signal()
    MQTT_REMOTE_TOPIC = "remotecommands/command"

    def __init__(self, app: QApplication, textBrowserHandler: TextBrowserHandler, initFileConfiguration: dict[str, str | float | int], *args, **kwargs):
        """
            Sets up the application for the Main GUI.

            :param app: The QT application that this should be set up against.
            :type app: QApplication
            :param textBrowserHandler: The logging handler that displays the logs onto the status box in the GUI.
            :type textBrowserHandler: TextBrowserHandler
            :param initFileConfiguration: The initialization configuration from the .ini file formatted as a dictionary.
            :type initFileConfiguration: dict[str, Any]
        """
        super().__init__(*args, **kwargs)
        self.setupUi(MainWindow = self)
        self.app = app

        # Set app on the top left of the screen
        screenRect = app.primaryScreen().geometry()
        self.move(screenRect.top(), screenRect.left())

        textBrowserHandler.textBrowser = self.statusTextBrowser

        self.legComboBoxL.currentIndexChanged.connect(self.toggleLegConfigurationVisibility)
        self.legComboBoxR.currentIndexChanged.connect(self.toggleLegConfigurationVisibility)
        self.legComboBoxL.currentIndexChanged.connect(lambda _ : self.displaySelectedLegText(self.legComboBoxL, True))
        self.legComboBoxR.currentIndexChanged.connect(lambda _ : self.displaySelectedLegText(self.legComboBoxR, False))

        self.colorActionGroup = PlotHelpers.setColorActionGroups(self)

        # Action for writing the changes to the Exo Controller.
        self.windowConfigurationButtons.writeChangesButton.clicked.connect(self.writeChangesToExoController)
        self.windowConfigurationButtons.writeAllChangesButton.clicked.connect(self.writeAllChangesToExoController)

        self.startStreamTime: float = 0 # This time is when the button is pressed to offset the times in the datasets (perf_counter and monotonic are not unix times).
        self.startStreamPushButton.toggled.connect(self.toggleStreaming)
        self.enableTorqueButton.toggled.connect(self.toggleTorque)

        # Action for reading changes from Exo controller.
        self.windowConfigurationButtons.readConfigurationButton.clicked.connect(self.readControllerConfiguration)
        self.windowConfigurationButtons.readAllConfigurationButton.clicked.connect(self.readAllControllerConfiguration)
    
        # Introspection on own instance variables.
        # Assumptions are that the widgets in the configuration end in "L" or "R"; otherwise should only have single field.
        self.configurationObjects: dict[str, QWidget] = InitFunc.setConfigurationDictionaries(PrefixNames.configurationWidgetNamePrefixes, self.configurationBox.__dict__)
        self.configurationObjects.update(InitFunc.setSingleConfigurationDictionaries(PrefixNames.configurationSingleWidgetNamePrefixes, self.configurationBox.__dict__))
        self.configurationLabels: dict[str, QLabel] = InitFunc.setConfigurationDictionaries(PrefixNames.configurationNameLabelPrefixes, self.configurationBox.__dict__)

        # Action for opening up JSON configuration file.
        self.windowConfigurationButtons.loadConfigurationFromFileButton.clicked.connect(self.openConfigurationFile)

        # Action for saving to JSON configuration file.
        self.windowConfigurationButtons.saveConfigurationToFileButton.clicked.connect(lambda: saveConfiguration(self, self.configurationObjects))

        self.initFileConfiguration = initFileConfiguration
        initFileDefaults: dict[str, float] = InitFunc.getDefaultsDictionary(self.initFileConfiguration)
        InitFunc.initializeLimits(self.initFileConfiguration.get('limits', {}), self.configurationObjects)
        InitFunc.initializeDefaultParameters(initFileDefaults, self.configurationObjects)
        InitFunc.initializeLegEntries(self.initFileConfiguration.get('leg', {}), self.legComboBoxL, self.legComboBoxR)

        self.graphContexts: list[GraphContext] = []
        self.currentContextIndex = 0
        self.MAX_TIME_RANGE = 10

        self.walkGraphContextIndex = ConfiguredWalkPlots.WalkPlotsPyQt.createGraphContext(self.graphContexts, self.plotTabWidget.walkFSM5GraphToggleHorizontalLayout, 
                                         self.plotTabWidget.walkFSM5GraphWidget, self.MAX_TIME_RANGE, initFileDefaults, simulator = False)

        self.proportionalGraphContextIndex = ConfiguredProportionalPlots.ProportionalPlotsPyQt.createGraphContext(self.graphContexts, self.plotTabWidget.proportionalGraphToggleHorizontalLayout, 
                                                               self.plotTabWidget.proportionalGraphWidget, self.MAX_TIME_RANGE, initFileDefaults, simulator = False)

        self.standingGraphContextIndex = ConfiguredStandingPlots.StandingPlotsPyQt.createGraphContext(self.graphContexts, self.plotTabWidget.standingGraphToggleHorizontalLayout,
                                                                     self.plotTabWidget.standingGraphWidget, self.MAX_TIME_RANGE, initFileDefaults, simulator = False)
        self.toggleLegConfigurationVisibility() # initialize visibility with the 0 index (None).

        PlotHelpers.createHidingBoxes(self, self.graphContexts)

        
        self.configurationBox.configurationTabs.currentChanged.connect(self.changeGraphContext)

        # Set the tabs as disabled so that they remain synchronized with the configuration table.
        for i in range(self.plotTabWidget.plotTabWidget.count()):
            self.plotTabWidget.plotTabWidget.setTabVisible(i, False)
        self.plotTabWidget.plotTabWidget.setCurrentIndex(self.currentContextIndex)

        # Due to a ongoing bug in Qt's Linux setting in Dark/Light mode,
        # we must rely on the panel's ability to change between Dark/Light mode.
        # Thus, this function is disabled in Linux
        # https://bugreports.qt.io/browse/QTBUG-129917
        if sys.platform == 'linux':
            self.actionLightMode.setDisabled(True)
            self.actionDarkMode.setDisabled(True)

        self.app.paletteChanged.connect(lambda _: PlotHelpers.changePlotBackground(self)) 
        PlotHelpers.changePlotBackground(self)

        # Graphing Stuff
        backend = 'pyqtgraph' if isinstance(self.plotTabWidget.walkFSM5GraphWidget, GraphicsLayoutWidget) else 'matplotlib'

        self.animatedGraphManager = AnimatedGraphManager(realTimeType = RealTimeType.SLIDING_WINDOW, backend = backend)
        fsm5GraphContext = self.graphContexts[self.walkGraphContextIndex]
        self.multiprocessingQueue = self.animatedGraphManager.getQueue()
        self.animatedGraphManager.addNewDatastream(fsm5GraphContext.fig, fsm5GraphContext.axes, FSM5, 
                                                                                fsm5GraphContext.axisLines[FSM5], MAX_TIME_RANGE = self.MAX_TIME_RANGE)
        
        proportionalGraphContext = self.graphContexts[self.proportionalGraphContextIndex]
        self.animatedGraphManager.addNewDatastream(proportionalGraphContext.fig, proportionalGraphContext.axes, Proportional, 
                                                                                proportionalGraphContext.axisLines[Proportional], MAX_TIME_RANGE = self.MAX_TIME_RANGE)
        
        standingGraphContext = self.graphContexts[self.standingGraphContextIndex]
        self.animatedGraphManager.addNewDatastream(standingGraphContext.fig, standingGraphContext.axes, Standing,
                                                                                standingGraphContext.axisLines[Standing], MAX_TIME_RANGE = self.MAX_TIME_RANGE)
       
        # Initialize with these off at first.
        for contexts in self.graphContexts:
            contexts.fig.toggleLeftLegs(False)
            contexts.fig.toggleRightLegs(False)

        self.multiprocessingQueue.cancel_join_thread()
        self.actionSaveData.triggered.connect(self.saveStreamedData)
        self.actionOpenData.triggered.connect(self.openPlotViewerWindow)
        self.actionOpenSimulator.triggered.connect(self.openSimulatorWindow)

        # Timer for drawing at 60 Hz (a little less based on the CoarseTimer and workload).
        self.drawTimer = QTimer()
        self.drawTimer.setInterval(1000/60)
        self.drawTimer.setTimerType(Qt.TimerType.CoarseTimer)
        self.drawTimer.timeout.connect(lambda: self.animatedGraphManager.qtDraw(self.graphContexts[self.currentContextIndex].fig))

        # Message that appears after 6 minutes signifying streaming has happened beyond usual amount of time (past 6 minute walk)
        self.sixMinuteWarningTimer = QTimer()
        self.sixMinuteWarningTimer.setTimerType(Qt.TimerType.VeryCoarseTimer) # (Background task)
        self.sixMinuteWarningTimer.setInterval(1000*60*6)
        self.sixMinuteWarningTimer.setSingleShot(True)
        self.sixMinuteWarningTimer.timeout.connect(self.warnSixMinuteStream)

        # External heartbeat (outside of the MQTT heartbeat) to verify that connection to server is still functional.
        self.heartbeatTimer = QTimer()
        self.heartbeatTimer.setTimerType(Qt.TimerType.VeryCoarseTimer)
        self.heartbeatTimer.setInterval(1000*15)
        self.heartbeatTimer.timeout.connect(self.timedHeartbeat)

        # Rewrite MQTT topic names if configured in the ini file, otherwise keep to hardcoded defaults.
        self.settings = InitFunc.getSettingsDictionary(self.initFileConfiguration)
        IDataProducer.DATA_TOPIC = self.settings.get("dataTopicName", IDataProducer.DATA_TOPIC)
        self.MQTT_REMOTE_TOPIC = self.settings.get('commandTopic', self.MQTT_REMOTE_TOPIC)
        self.remoteHostTopic = Template(self.settings.get('remoteHostTopic', 'remotecommands/return/$hostname')).substitute(hostname = socket.gethostname())
        self.hasTrigger = self.settings.get('hasTrigger', False)

        if self.hasTrigger:
            ButtonPress.TRIGGER_TOPIC = self.settings.get('triggerTopicName', ButtonPress.TRIGGER_TOPIC)
            # Trigger doesn't have a figure or axes, just passing in something irrelevant.
            self.animatedGraphManager.addNewDatastream(fsm5GraphContext.fig, fsm5GraphContext.axes, Trigger, 
                                                                                fsm5GraphContext.axisLines[Trigger], MAX_TIME_RANGE = self.MAX_TIME_RANGE)
            self.triggerPressSignal.connect(self.checkButtonPress)

        self.isCalibrated = False
        self.setCalibrationButton.pressed.connect(self.runCalibration)

        # Parameters for reading from multiprocessing queue.
        self.MAX_CLEAR_THREADS = 10
        self.MAX_GRAPH_THREADS = 1 # 1 graph thread seems to be enough with MQTT integration.

        # Stuff to connect to the Raspberry Pi using mosquitto server
        self.remoteReturnQueue = Queue()
        self.isConnected = False

        self.connectToRaspberryPiButton.pressed.connect(self.connectToRemoteManager) 
        self.toggleWidgetsWhenConnected(disabled = True)

        self.mqttClient = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        self.mqttClient.on_connect = self.onConnect
        self.mqttClient.on_message = self.onMessage

    @override
    def closeEvent(self, event):
        # This closeEvent runs when the X is pressed. We need to stop the drawing to prevent
        # the threads from continuing to run afterwards preventing exiting from properly happening.
        self.sendRemoteCommand('stopSend', {}) # Send stop on exit, if it can.
        self.stopDrawing() # Stop processing data to prevent threads from continuing.
        return super().closeEvent(event)
    
    def onConnect(self, client: mqtt.Client, userdata, flags, reason_code, properties):
        logger.debug(f"Connected with result code {reason_code}")
        # Subscribing in onConnect() means that if we lose the connection and
        # reconnect then subscriptions will be renewed.
        topicsToSubscribe = [IDataProducer.DATA_TOPIC, ButtonPress.TRIGGER_TOPIC, self.remoteHostTopic]
        for topic in topicsToSubscribe:
            client.subscribe(topic)
        logger.debug("Subscribed to: " + ",".join(topicsToSubscribe))
        
    # The callback for when a PUBLISH message is received from the server.
    def onMessage(self, client: mqtt.Client, userdata, msg: mqtt.MQTTMessage):
        if msg.topic == IDataProducer.DATA_TOPIC:
            self.multiprocessingQueue.put_nowait(msg.payload) # Unpickling is responsibility of the workers.
        elif msg.topic == ButtonPress.TRIGGER_TOPIC:
            self.triggerPressSignal.emit() # No real data, just emit that it has sent.
        elif self.remoteHostTopic in msg.topic:
            self.remoteReturnQueue.put_nowait(msg.payload)

    @Slot()
    def connectToRemoteManager(self) -> None:
        """
            Connects to the remote, setting up the MQTT client and checking with a heartbeat to determine
            whether or not the remote can be reached. Widgets are toggled accordingly.

            :return: None
            :rtype: None
        """

        if not self.isConnected:
            try:

                # Keep-alive = 0 means no attempt to check for pings, but this has to be set in the mosquitto.conf file.
                # Max is 65335 seconds = 18.2 hours.
                self.mqttClient.connect(self.settings['hostAddress'], self.settings['hostPort'], keepalive = 60)
                logger.info("Successfully connected to {0} MQTT at port {1}".format(self.mqttClient.host, self.mqttClient.port))
                self.mqttClient.loop_start()

                self.isConnected = True
                # First heartbeat check to verify whether server process is on.
                self.heartbeat()
                self.heartbeatTimer.start()

                self.toggleWidgetsWhenConnected(disabled = False)
                self.connectLegComboBoxRemoteSlot() # Only set changing of slot if it can connect to the remote.
                
                # Change logic controller to current selected (in case remote was restart), this changes to current tab.
                # This ensures that it will be on the right one especially when the GUI was restart, but the Raspberry Pi process was not.
                controlLogicType = self.graphContexts[self.currentContextIndex].controlLogicType
                self.sendRemoteCommand('changeControlLogic', {'controlLogicType': controlLogicType})
            except socket.gaierror:
                logger.error("Failed to connect to {0} at port {1}. Check LAN connection and firewall settings.".format(self.mqttClient.host, self.mqttClient.port))
            except ConnectionRefusedError:
                logger.error("ConnectionRefusedError: Is the Raspberry Pi server process on?")
                self.handleDisconnection()
        else:
            logger.warning("Connection is already established.")

    def connectLegComboBoxRemoteSlot(self) -> None:
        """
            Connects the leg MQTT is connected.

            :return: None
            :rtype: None
        """
        self.legComboBoxL.currentIndexChanged.connect(self.turnControllerLeg)
        self.legComboBoxR.currentIndexChanged.connect(self.turnControllerLeg)

    def disconnectLegComboBoxRemoteSlots(self) -> None:
        """
            Temporarily disconnects the leg from turning on/off when disconnected. 
            This prevents trying to turning off when already disconnected.

            :return: None
            :rtype: None
        """
        self.legComboBoxL.currentIndexChanged.disconnect(self.turnControllerLeg)
        self.legComboBoxR.currentIndexChanged.disconnect(self.turnControllerLeg)

    @Slot()
    def timedHeartbeat(self) -> None:
        """
            Attempts at least two retries of the periodic heartbeat before a disconnection occurs.

            :return: None
            :rtype: None
        """
        NUM_RETRIES = 2
        successfulHeartBeat = False
        retries = 0
        while not successfulHeartBeat and retries < NUM_RETRIES:  
            try:
                self.heartbeat()
                logger.debug(f"Successful heartbeat at {datetime.now().strftime('%H:%M:%S.%f')}")
                successfulHeartBeat = True
            except ConnectionRefusedError:
                retries = retries + 1
        
        if not successfulHeartBeat:
            logger.error("Disconnecting from Raspberry Pi server process.")
            self.handleDisconnection()
        
    def heartbeat(self) -> None:
        """
            Sends a periodic heartbeat command, comparing the received response to a desired "ACK". Raises
            ConnectionRefusedError if not received timely enough.
            
            :return: None
            :rtype: None
        """
        if self.sendRemoteCommand(sentFunction = "heartbeat", sentParameters = {"syn": "SYN"}, logComment = False) != "ACK":
            raise ConnectionRefusedError("Failed heartbeat.")

    def handleDisconnection(self) -> None:
        """
            Attempts to gracefully handle disconnections, particularly when the heartbeat commands fail,
            this attempts to reset the GUI state back to the beginning as much as possible.

            :return: None
            :rtype: None
        """
        # A disconnection == everything is disconnected except the torque and streaming.
        # Therefore you would get deadlock when torque and streaming is still running (and locking the rest of the configuration)
        # but you cannot stop the streaming because the configuration is locked with None for the legs. This breaks that, but
        # will attempt to send commands even though connection hasn't been resolved because setChecked runs the slot. May be worth it to
        # temporarily stop it to set the uncheck.
        if self.enableTorqueButton.isChecked():
            self.enableTorqueButton.setChecked(False)
        
        if self.startStreamPushButton.isChecked():
            self.startStreamPushButton.setChecked(False)
        self.stopDrawing()

        self.isConnected = False
        self.heartbeatTimer.stop()
        self.toggleWidgetsWhenConnected(disabled = True)
        self.disconnectLegComboBoxRemoteSlots() # Disable turning the control of the leg so that None does not try to change already disconnected remote.
        self.legComboBoxL.setCurrentIndex(0) # Set the leg combo boxes to None, so reconnection will force reset.
        self.legComboBoxR.setCurrentIndex(0)
        self.mqttClient.loop_stop()
        
    @Slot()
    def saveStreamedData(self) -> None:
        """
            Saves the streamed data to disk, reading in the current controller configuration from remote.

            :return: None
            :rtype: None
        """
        if not self.startStreamPushButton.isChecked():
            SaveDialog.saveStreamedData(self, self.animatedGraphManager, self.startStreamTime, ControlLogicEnum)
        else:
            logger.warning("Stream is currently ongoing. Please stop stream to save streamed data.")

    @Slot()
    def openPlotViewerWindow(self) -> None:
        """
            Opens up a plot viewer in a separate window. Will not open if the stream is still on.

            :return: None
            :rtype: None
        """
        if not self.startStreamPushButton.isChecked():
            plotWindow = PlotWindow(self)
            plotWindow.openDataset()
            plotWindow.show()
        else:
            logger.warning("Stream is currently ongoing. Please stop stream to open dataset.")

    @Slot()
    def openSimulatorWindow(self) -> None:
        """
            Opens a simulator window in a separate window. Will not open if the stream is still on.
            
            :return: None
            :rtype: None
        """
        if not self.startStreamPushButton.isChecked():
            simWindow = Simulator(self.app, self.initFileConfiguration)
            simWindow.show()
        else:
            logger.warning("Stream is currently ongoing. Please stop stream to open simulator.")
    
    @Slot()
    def checkButtonPress(self) -> None:
        """
            Callback that displays whether the synchronization trigger has been pressed.

            :return: None
            :rtype: None
        """
        logger.info(redBoldText("Trigger has been pressed."))

    def sendRemoteCommand(self, sentFunction: str, sentParameters: dict[str, Any], logComment: bool = True) -> Any | None:
        """
            Function that sends the remote command (RPC), waiting until it receives a return value from the remote.
            This runs by publishing and receiving MQTT messages. These values are pickled, thus typing should be preserved.

            :param sentFunction: The function to be called on the remote side.
            :type sentFunction: str
            :param sentParameters: A dictionary containing the parameters to be sent with the sentFunction.
            :type sentParameters: dict[str, Any]
            :param logComment: Whether or not the comment should be logged into the file and status console.
            :type logComment: bool
            
            :return: Anything from the return of the remote command.
            :rtype: Any | None
        """
        if self.isConnected:
            try:
                self.mqttClient.publish(topic = self.MQTT_REMOTE_TOPIC, payload = pickle.dumps((socket.gethostname(), sentFunction, sentParameters)), qos = 2)
                returnValue = pickle.loads(self.remoteReturnQueue.get(timeout = 5))

                if logComment:
                    logger.debug(f"Sent command: {sentFunction}")
                return returnValue
            except (ConnectionResetError, ConnectionAbortedError, EOFError):
                logger.error("Connection was forcibly closed by remote host.")
                self.handleDisconnection()
            except Empty:
                if logComment:
                    logger.error(f"Failed to receive response back to {sentFunction} with parameters {sentParameters}.")
        else:
            logger.debug("Not connected to server.")
    
    def toggleWidgetsWhenConnected(self, disabled: bool) -> None:
        """
            Toggles the widget to enabled when connected, and disabled when disconnected.

            :param disabled: Whether or not the widgets should be enabled or disabled.
            :type disabled: bool

            :return: None
            :rtype: None
        """
        self.calibrationGroupBox.setDisabled(disabled)
        self.configurationBox.setDisabled(disabled)
        self.sessionGroupBox.setDisabled(disabled)
        self.legUsedGroupBox.setDisabled(disabled)
    
    def readControllerConfigurationRemote(self, controlLogicType: ControlLogicEnum, formatForConfiguration: bool) -> dict:
        """
            Reads the controller configuration from the remote with the given control logic type, optionally formatted for
            saved stream file.

            :param controlLogicType: An IntEnum that references a type on the remote side for a given control logic type.
            :type controlLogicType: ControlLogicEnum
            :param formatForConfiguration: Whether or not this configuration should be used in a saved stream file (strings are saved for state names).
            :type formatForConfiguration: bool

            :return: A dictionary containing the configuration information for this control logic type.
            :rtype: dict[str, Any]
        """
        return self.sendRemoteCommand('getConfigurationParameters', {'controlLogicType': controlLogicType, 'formatForConfiguration': formatForConfiguration})

    def readControllerApiEvents(self) -> list[tuple[float, str, dict]]:
        """
            Gets the API Events that were called since the last remote start time update.
        
            :return: A list of tuples containing the time, name, and parameters of the event.
            :rtype: list[tuple[float, str, dict]]
        """
        return self.sendRemoteCommand('exportAPICallEvents', {})
    
    def _updateFromReadControllerConfiguration(self, contextIndex: int) -> None:
        # Calls the respective defined methods in the GraphContext for reading the configuration functions.
        # only performs them if the leg is active however.
        controlLogicType = self.graphContexts[contextIndex].controlLogicType
        leftLegConfiguration, rightLegConfiguration = self.readControllerConfigurationRemote(controlLogicType, False)
        readConfigurationFromControllerFunc = self.graphContexts[contextIndex].readConfigurationFromControllerFunc

        if self.isLeftLegActive():
            readConfigurationFromControllerFunc(self, leftLegConfiguration, True)
        
        if self.isRightLegActive():
            readConfigurationFromControllerFunc(self, rightLegConfiguration, False)

    @Slot()
    def readControllerConfiguration(self) -> None:
        """
            Reads the current configuration from the controller and updates the configuration
            box in the GUI.

            :return: None
            :rtype: None
        """
        self._updateFromReadControllerConfiguration(self.currentContextIndex)

    @Slot()
    def readAllControllerConfiguration(self) -> None:
        """
            Reads all of the configuration from the remote and updates the configuration box
            in the GUI.

            :return: None
            :rtype: None
        """
        for i in range(len(self.graphContexts)):
            self._updateFromReadControllerConfiguration(i)

    # Change the controller to on/off when None is selected. If it's selected to something valid, then change the exoLeg parameters.
    @Slot()
    def turnControllerLeg(self) -> None:
        """
            Turns the leg on the remote when a leg is selected (or off if None is selected).
            If starting the leg fails, then it is reverted back to None and turned off in the remote.

            :return: None
            :rtype: None
        """
        def turnLeg(legActive: bool, comboBox: QComboBox, index: int) -> bool:
            if legActive:
                legName = comboBox.currentText() # Match based on the text of the combo box.
                legExtensionPositive = self.initFileConfiguration['leg'][legName]['isExtensionPositive']
                self.sendRemoteCommand('setControllerLegExtensionPositive', {'index': index, 'isExtensionPositive': legExtensionPositive})
                return self.sendRemoteCommand('turnOnOffControllerRobot', {'index': index, 'enable': True})
            else:
                return self.sendRemoteCommand('turnOnOffControllerRobot', {'index': index, 'enable': False})

        isSuccessfulLeft = turnLeg(self.isLeftLegActive(), self.legComboBoxL, PrefixNames.getLeftRightIndex(True)) # May be better to have this as one remote function call.
        if not isSuccessfulLeft:
            logger.error("Failed to turn on left leg. Is the left leg connected? Reverting selection back.")
            self.legComboBoxL.setCurrentIndex(0) # Revert it back to none because of failed selection.

        isSuccessfulRight = turnLeg(self.isRightLegActive(), self.legComboBoxR, PrefixNames.getLeftRightIndex(False))
        if not isSuccessfulRight:
            logger.error("Failed to turn on right leg. Is the right leg connected? Reverting selection back.")
            self.legComboBoxR.setCurrentIndex(0) # Revert it back to none because of failed selection.


    @Slot()
    def runCalibration(self) -> None:
        """
            Runs the calibration command on the remote. This unlocks the torque and streaming buttons if at least one
            leg is calibrated.

            :return: None
            :rtype: None
        """
        self.sendRemoteCommand('calibrateRobots', {})

        if not self.isCalibrated:
            self.isCalibrated = True
            self.setCalibrationButton.setText("Set Full Knee Extension (again)")
            
            # At least one calibration must be performed before streaming and enable torque buttons can be accessed.
            self.enableTorqueButton.setEnabled(True)
            self.startStreamPushButton.setEnabled(True)

        logger.info("Calibration has been set.")

    @Slot(int)
    def changeGraphContext(self, configurationPageIndex: int) -> None:
        """
            Changes the set of functions and graphs to a specific page for respective controller. Performed
            when the configuration tab is changed to a differnet controller.

            :param configurationPageIndex: the index that the configuration has changed into.
            :type configurationPageIndex: int
            
            :return: None
            :rtype: None
        """
        pageToSwitch = configurationPageIndex if configurationPageIndex < len(self.graphContexts) else 0
        self.plotTabWidget.plotTabWidget.setCurrentIndex(pageToSwitch)
        self.currentContextIndex = pageToSwitch # Kind of iffy way to handle non-existing contexts.
        
        # Change logic controller.
        controlLogicType = self.graphContexts[self.currentContextIndex].controlLogicType
        self.sendRemoteCommand('changeControlLogic', {'controlLogicType': controlLogicType})

    def isLeftLegActive(self) -> bool:
        """
            Determines whether the left leg is active (index 0 is assumed None)./s

            :return: Whether left leg is active
            :rtype: bool 
        """
        return self.legComboBoxL.currentIndex() != 0
    
    def isRightLegActive(self) -> bool:
        """
            Determines whether the right leg is active (index 0 is assumed None).

            :return: Whether right leg is active
            :rtype: bool
        """
        return self.legComboBoxR.currentIndex() != 0

    def _updateWriteChangesControllerConfiguration(self, contextIndex: int) -> None:
        # Runs the actual remote command, validating the configuration, and adjusting the plots as necessary.
        currentContext = self.graphContexts[contextIndex]
        leftConfigurationChanges, rightConfigurationChanges = currentContext.getConfigurationChangesFunc(self.configurationObjects, self.configurationBox)
        if (currentContext.validateConfigurationFunc(self.configurationBox, self.isLeftLegActive(), True, leftConfigurationChanges) &
                           currentContext.validateConfigurationFunc(self.configurationBox, self.isRightLegActive(), False, rightConfigurationChanges)): # & prevents short circuit evaluation.
            currentContext.writeConfigurationChangesFunc(self, leftConfigurationChanges, rightConfigurationChanges)
            currentContext.adjustPlotThresholdValuesFunc(self, leftConfigurationChanges, rightConfigurationChanges)
            logger.info("Changes written to Exoskeleton Controller.")
        else:
            logger.info("Errors found in Configuration. See above for more info.")

    @Slot()
    def writeChangesToExoController(self) -> None:
        """
            Writes the current changes of the current controller to the remote.

            :return: None
            :rtype: None
        """
        self._updateWriteChangesControllerConfiguration(self.currentContextIndex)

    @Slot()
    def writeAllChangesToExoController(self) -> None:
        """
            Writes all changes for each controller to the remote.

            :return: None
            :rtype: None
        """
        for i in range(len(self.graphContexts)):
            self._updateWriteChangesControllerConfiguration(i)

    @Slot()
    def warnSixMinuteStream(self) -> None:
        """
            Callback to warn the user that streaming has passed the 6-minute window (max for 6-minute walk test).

            :return: None
            :rtype: None
        """
        logger.warning(datetime.now().strftime("Stream has been run for 6 minutes at %H:%M:%S."), extra = {TextBrowserHandler.RED_WARN: True})

    @Slot()
    def toggleLegConfigurationVisibility(self) -> None:
        """
            Toggles the left and right leg visibility in the widgets, graphs.
            If both legs are not selected then calibration buttons, torque, and streaming buttons are
            also greyed out.

            :return: None
            :rtype: None
        """
        hideLeftLegConfiguration = not self.isLeftLegActive() # First element will always be 'None'.
        hideRightLegConfiguration = not self.isRightLegActive()

        legWidgets = {**self.configurationObjects, **self.configurationLabels}
        for configurationWidgetName, configurationWidgetObject in legWidgets.items():
            hideItem(configurationWidgetName, configurationWidgetObject, hideLeftLegConfiguration, hideRightLegConfiguration)

        # Update the contexts so that they are visible on turn on.
        for contexts in self.graphContexts:
            contexts.fig.toggleLeftLegs(not hideLeftLegConfiguration)
            contexts.fig.toggleRightLegs(not hideRightLegConfiguration)

        # Also disable the save configuration, read, and write changes button if both are None.
        disableButtons = hideLeftLegConfiguration and hideRightLegConfiguration
        self.windowConfigurationButtons.toggleDisabledConfigurationWidgets(disableButtons)
        self.setCalibrationButton.setDisabled(disableButtons)

        if disableButtons:
            self.isCalibrated = False
            self.setCalibrationButton.setText("Set Full Knee Extension")
            self.enableTorqueButton.setDisabled(disableButtons)
            self.startStreamPushButton.setDisabled(disableButtons)

    @Slot(QComboBox, bool)
    def displaySelectedLegText(self, legComboBox: QComboBox, isLeft: bool) -> None:
        """
            Displays text on which leg was selected (using the ID name).

            :param legComboBox: The combobox where a leg was selected.
            :type legComboBox: QComboBox
            :param isLeft: Whether or not this is a left leg.
            :type isLeft: bool
            :return: None
            :rtype: None
        """
        side = PrefixNames.getLegSideLong(isLeft).lower()
        logger.info(f"[{legComboBox.currentText()}] selected on {side} side.")
    
    def toggleDisabledConfigurationWidgets(self, disabled: bool) -> None:
        """
            Toggles the configuration widgets, locking them down if streaming or torque is
            currently on.

            :param disabled: Whether or not the configruation objects should be locked down (greyed out).
            :type disabled: bool

            :return: None
            :rtype: None 
        """
        for configurationWidgetObject in self.configurationObjects.values():
            configurationWidgetObject.setDisabled(disabled)
        self.legComboBoxL.setDisabled(disabled)
        self.legComboBoxR.setDisabled(disabled)
        self.windowConfigurationButtons.toggleDisabledConfigurationWidgets(disabled = disabled)
        self.setCalibrationButton.setDisabled(disabled)

    def stopDrawing(self) -> None:
        """
            Stops the drawing, stopping all timers.
            
            :return: None
            :rtype: None
        """
        self.animatedGraphManager.isStreaming.set()
        self.drawTimer.stop()
        self.sixMinuteWarningTimer.stop()

    @Slot()
    def toggleStreaming(self, isChecked: bool) -> None:
        """
            Toggles the streaming on and off to enable data transfer from the remote to client.
            When streaming is ended, the user is asked whether or not it should be saved.

            :param isChecked: Whether or not the startStreamPushButton has been clicked as a button.
            :type isChecked: bool
            
            :return: None
            :rtype: None
        """
        if isChecked:
            self.startStreamPushButton.setText("Stop Stream")
            logger.info("Stream has been started.")

            self.toggleDisabledConfigurationWidgets(disabled = True)

            # Clear out the queue before running processes.
            self.sendRemoteCommand('stopSend', {}) # Stop sending first to make sure it's off.
            logger.debug("Clearing controller data queue.")
            with ThreadPoolExecutor() as executor: # Multiple threads to clear the queues quickly.
                for i in range(self.MAX_CLEAR_THREADS):
                    executor.submit(self.animatedGraphManager.clearQueues)
            self.animatedGraphManager.reset()
            self.resetAllGraphLimits() # Reset the x-limits of each of the graphs.
            
            self.sendRemoteCommand('restartSharedStartTime', {}) # Restart the time on the controller side.
            self.startStreamTime = time.time()
            self.sendRemoteCommand('startSend', {}) # Start streaming on the controller side. Also handles the Trigger streaming.

            # Multiple threads to update the data buffers with data points.
            executor = ThreadPoolExecutor()
            for i in range(self.MAX_GRAPH_THREADS):
                executor.submit(self.animatedGraphManager.qtRun)
            executor.shutdown(wait = False) # wait = False prevents blocking (the threads end when isStreaming flag is set).
            
            self.drawTimer.start()
            self.sixMinuteWarningTimer.start()

        else:
            self.startStreamPushButton.setText("Start Stream")
            logger.info("Stream has been stopped.")

            self.sendRemoteCommand('stopSend', {}) # Stop streaming on the controller side. Also handles the Trigger streaming
            self.stopDrawing()
            
            # Keep it disabled if the torque button is checked.
            if not self.enableTorqueButton.isChecked():
                self.toggleDisabledConfigurationWidgets(disabled = False)

            elapsed_time = time.perf_counter() - self.animatedGraphManager.performanceTimer
            logger.debug(f"FPS: {self.animatedGraphManager.getCounter()/elapsed_time}.")
            self.animatedGraphManager.drawFinalGraph()

            saveDialog = SaveDialog(self, self.animatedGraphManager, self.startStreamTime, ControlLogicEnum)
            saveDialog.setWindowTitle("Save stream data?")
            saveDialog.exec()

    def resetAllGraphLimits(self) -> None:
        """
            Reset the graph limits to originally prescribed values defined by the user through the GraphContext function.
            
            :return: None
            :rtype: None
        """
        for graphContext in self.graphContexts:
            graphContext.resetGraphLimitsFunc(graphContext.axes, self.MAX_TIME_RANGE)

    @Slot()
    def toggleTorque(self, isChecked: bool) -> None:
        """
            Toggles the torque button, changing the text and sending the remote command.

            :param isChecked: Whether or not the enableTorqueButton is checked.
            :type isChecked: bool
            
            :return: None
            :rtype: None
        """
        if isChecked:
            self.enableTorqueButton.setText("Disable Torque")
            logger.info("Torque has been enabled.")
            self.toggleDisabledConfigurationWidgets(disabled = True)
            self.sendRemoteCommand('enableActuation', {'enable': True})
        else:
            self.enableTorqueButton.setText("Enable Torque")
            logger.info("Torque has been disabled.")

            # Keep it disabled if the streaming button is checked.
            if not self.startStreamPushButton.isChecked():
                self.toggleDisabledConfigurationWidgets(disabled = False)
            self.sendRemoteCommand('enableActuation', {'enable': False})

    @Slot()
    def openConfigurationFile(self) -> None:
        """
            Opens a file dialog to open up a JSON configuration file, then loads the values.
            Only Comboboxes and spinboxes are currently used in the configuration box.

            :return: None
            :rtype: None
        """
        options = QFileDialog.Option() # Must use DontUseNativeDialog for other options to work.
        fileName, _ = QFileDialog.getOpenFileName(self, "Load Configuration File", "", "JSON Files (*.json)", options = options)
        
        if fileName:
            try:
                with open(fileName, 'r') as loadedConfigurationFile:
                    loadedConfigurationData = json.load(loadedConfigurationFile)
                    logger.info(f"Loaded Configuration File: {fileName}.")
                    for name, value in loadedConfigurationData.items():
                        configurationObject = self.configurationObjects.get(name)
                        if isinstance(configurationObject, QComboBox):
                            configurationObject.setCurrentIndex(value)
                        elif isinstance(configurationObject, QAbstractSpinBox):
                            configurationObject.setValue(value)
            except OverflowError:
                if isinstance(configurationObject, QAbstractSpinBox):
                    logger.error(f"Configuration '{name}' with value {value} is not within bounds " + 
                             f"[{configurationObject.minimum()}, {configurationObject.maximum()}].")
            except FileNotFoundError: # QFileDialog prevents trying nonexisting files.
                logger.error(f"Error Loading Configuration File: {fileName}.")

    @Slot()
    def changeStyle(self) -> None:
        """
            Changes the light/dark mode of the window.

            :return: None
            :rtype: None
        """
        if self.actionSystemDefault.isChecked():
            colorMode = "System Default"
            colorToSet = Qt.ColorScheme.Unknown
        elif self.actionLightMode.isChecked():
            colorMode = "Light Mode"
            colorToSet = Qt.ColorScheme.Light
        elif self.actionDarkMode.isChecked():
            colorMode = "Dark Mode"
            colorToSet = Qt.ColorScheme.Dark
        
        self.app.styleHints().setColorScheme(colorToSet)
        logger.info(f"Changed to {colorMode}.")