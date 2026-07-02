import pickle
from queue import Queue, Empty
from typing import Any, override
from PySide6.QtCore import QTimer, Slot, Qt, Signal
from PySide6.QtWidgets import QMainWindow, QWidget, QApplication, QComboBox, QAbstractSpinBox
from brace.UI.GraphContext import GraphContext
from brace.example.zaber.ZaberWindow import Ui_ZaberWindow
from pyqtgraph import GraphicsLayoutWidget, PlotItem
from datetime import datetime
import logging
import time
from brace.UI.LoggingHelpers import redBoldText, TextBrowserHandler
import numpy as np
from matplotlib.axes import Axes
from brace.RealTimeGraphing.Graphing.IDataProducer import IDataProducer
import brace.UI.example.GUIController.PrefixNames as PrefixNames
import brace.example.zaber.ConfiguredProportionalPlots as ConfiguredProportionalPlots

from paho.mqtt import client as mqtt
from concurrent.futures import ThreadPoolExecutor
import socket

from brace.RealTimeGraphing.Graphing.AnimatedGraphManager import AnimatedGraphManager, RealTimeType
from brace.example.zaber.ZaberControlLogic import ControlLogic, ZaberData
from brace.Server.GPIOSynch.PushButton import ButtonPress

import logging
logger = logging.getLogger("logger")

def onConnect(client, userdata, flags, reason_code, properties):
    logger.debug(f"Connected with result code {reason_code}")
    # Subscribing in onConnect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    remoteLoggerHostTopic = f"remotecommands/return/{socket.gethostname()}"
    topicsToSubscribe = [IDataProducer.DATA_TOPIC, ButtonPress.TRIGGER_TOPIC, remoteLoggerHostTopic]
    for topic in topicsToSubscribe:
        client.subscribe(topic)
    logger.debug("Subscribed to: " + ",".join(topicsToSubscribe))

class UnableToTurnOnError(BaseException):
    """ Raised when unable to turn on controller. """
        
class ZaberMainWindow(QMainWindow, Ui_ZaberWindow):
    """
        Main GUI for the Mechanical Actuation for Unpleasant Stimulus (MAUS) device
        This class handles the main functionality for the GUI elements.
    """
    triggerPressSignal = Signal()
    MQTT_REMOTE_TOPIC = "remotecommands/command"

    configurationWidgetNamePrefixes = []
    configurationSingleWidgetNamePrefixes = []
    def __init__(self, app: QApplication, textBrowserHandler: TextBrowserHandler, *args, **kwargs):
        """
            :param app: The application that is spawning in this GUI.
            :type app: QApplication
            :param textBrowserHandler: The logging handler that should write to the text box in the GUI.
            :type textBrowserHandler: TextBrowserHandler
        """
        super().__init__(*args, **kwargs)
        self.setupUi(ZaberWindow = self)
        self.app = app

        # Set app on the top left of the screen
        screenRect = app.primaryScreen().geometry()
        self.move(screenRect.top(), screenRect.left())

        textBrowserHandler.textBrowser = self.statusTextBrowser

        # Action for writing the changes to the Exo Controller.
        self.writeChangesButton.clicked.connect(self.writeChangesToExoController)

        self.startStreamTime: float = 0 # This time is when the button is pressed to offset the times in the datasets (perf_counter and monotonic are not unix times).
        self.startStreamPushButton.toggled.connect(self.toggleStreaming)
        self.enableActuationButton.toggled.connect(self.toggleActuation)

        self.readConfigurationButton.clicked.connect(self.readControllerConfiguration)

        self.graphContexts: list[GraphContext] = []
        self.currentContextIndex = 0
        self.MAX_TIME_RANGE = 10

        ConfiguredProportionalPlots.ProportionalPlotsPyQt.createGraphContext(self.graphContexts, self.proportionalGraphToggleHorizontalLayout,
                                                                             self.proportionalGraphWidget, self.MAX_TIME_RANGE)
        
        for graphContext in self.graphContexts:
            axes = graphContext.axes
            self.showBottomRowLabel(axes)

        self.configurationTabs.currentChanged.connect(self.changeGraphContext)
        self.plotTabWidget.setCurrentIndex(self.currentContextIndex)

        # Graphing Stuff
        backend = 'pyqtgraph' if isinstance(self.proportionalGraphWidget, GraphicsLayoutWidget) else 'matplotlib'

        self.animatedGraphManager = AnimatedGraphManager(realTimeType = RealTimeType.SLIDING_WINDOW, backend = backend)
        self.multiprocessingQueue = self.animatedGraphManager.getQueue()
        
        proportionalGraphContext = self.graphContexts[0]
        self.animatedGraphManager.addNewDatastream(proportionalGraphContext.fig, proportionalGraphContext.axes, ZaberData, 
                                                                                proportionalGraphContext.axisLines[ZaberData], MAX_TIME_RANGE = self.MAX_TIME_RANGE)

        self.multiprocessingQueue.cancel_join_thread()

        # Timer for drawing at 60 Hz (a little less based on the CoarseTimer and workload).
        self.drawTimer = QTimer()
        self.drawTimer.setInterval(1000/60)
        self.drawTimer.setTimerType(Qt.TimerType.CoarseTimer)
        self.drawTimer.timeout.connect(lambda: self.animatedGraphManager.qtDraw(self.graphContexts[self.currentContextIndex].fig))

        # External heartbeat (outside of the MQTT heartbeat) to verify that connection to server is still functional.
        self.heartbeatTimer = QTimer()
        self.heartbeatTimer.setTimerType(Qt.TimerType.VeryCoarseTimer)
        self.heartbeatTimer.setInterval(1000*15)
        self.heartbeatTimer.timeout.connect(self.timedHeartbeat)
        
        # External Trigger Press
        self.triggerPressSignal.connect(self.checkButtonPress)

        self.isCalibrated = False
        self.setCalibrationButton.pressed.connect(self.runCalibration)

        # Parameters for reading from multiprocessing queue.
        self.MAX_CLEAR_THREADS = 10
        self.MAX_GRAPH_THREADS = 1 # 1 graph thread seems to be enough with MQTT integration.

        # Stuff to connect to the Raspberry Pi using mosquitto server
        self.remoteReturnQueue = Queue()
        self.isConnected = False

        self.connectToZaberButton.pressed.connect(self.connectToRemoteManager) 
        self.toggleWidgetsWhenConnected(disabled = True)

        self.invertPushButton.pressed.connect(self.invertPosition)

        self.mqttClient = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        self.mqttClient.on_connect = onConnect
        self.mqttClient.on_message = self.onMessage

    @override
    def closeEvent(self, event):
        """
            Runs shutdown callbacks when the X is pressed on the GUI.
            Turns off the robot and stops streaming from the remote.
        """
        # This closeEvent runs when the X is pressed. We need to stop the drawing to prevent
        # the threads from continuing to run afterwards preventing exiting from properly happening.
        self.sendRemoteCommand('turnOnOffControllerRobot', {'index': 0, 'enable': False})
        self.sendRemoteCommand('stopSend', {}) # Send stop on exit, if it can.
        self.stopDrawing() # Stop processing data to prevent threads from continuing.
        return super().closeEvent(event)
        
    # The callback for when a PUBLISH message is received from the server.
    def onMessage(self, client: mqtt.Client, userdata, msg: mqtt.MQTTMessage):
        # Messages are placed into one of three topics, the DATA_TOPIC for streamed data,
        # the TRIGGER_TOPIC for receiving when the button was triggered, and remotecommands/return/
        # for return values.
        if msg.topic == IDataProducer.DATA_TOPIC:
            self.multiprocessingQueue.put_nowait(msg.payload) # Unpickling is responsibility of the workers.
        elif msg.topic == ButtonPress.TRIGGER_TOPIC:
            self.triggerPressSignal.emit() # No real data, just emit that it has sent.
        elif "remotecommands/return/" in msg.topic:
            self.remoteReturnQueue.put_nowait(msg.payload)

    @Slot()
    def connectToRemoteManager(self) -> None:
        """
            Connects to the remote by first connecting to the MQTT server,
            and attempting an initial heartbeat to determine whether the server on the
            remote is on and ready.

            :return: None
            :rtype: None
        """
        if not self.isConnected:
            try:
                self.mqttClient.connect('raspberrypi', 8080, keepalive = 60)
                logger.info("Successfully connected to {0} MQTT at port {1}".format(self.mqttClient.host, 8080))
                self.mqttClient.loop_start()

                self.isConnected = True
                # First heartbeat check to verify whether server process is on.
                self.heartbeat()
                self.heartbeatTimer.start()

                self.sendRemoteCommand('setControllerLegExtensionPositive', {'index': 0, 'isExtensionPositive': True})
                isSuccessfulTurnOn = self.sendRemoteCommand('turnOnOffControllerRobot', {'index': 0, 'enable': True})

                if not isSuccessfulTurnOn:
                    raise UnableToTurnOnError("Failed to turn on Zaber controller. Is everything connected properly?")

                self.toggleWidgetsWhenConnected(disabled = False)
            except socket.gaierror:
                logger.error("Failed to connect to {0} at port {1}. Check LAN connection and firewall settings.".format(self.mqttClient.host, 8080))
            except ConnectionRefusedError:
                logger.error("ConnectionRefusedError: Is the Raspberry Pi server process on?")
                self.handleDisconnection()
            except UnableToTurnOnError as ex:
                logger.error(ex.args)
                self.handleDisconnection()
        else:
            logger.warning("Connection is already established.")

    @Slot()
    def invertPosition(self) -> None:
        """
            Inverts the retraction/extension actuation convention on the remote side.

            :return: None
            :rtype: None
        """
        self.sendRemoteCommand('setControllerLegExtensionPositive', {'index': 0, 'isExtensionPositive': self.invertPushButton.isChecked()})

    @Slot()
    def timedHeartbeat(self) -> None:
        """
            Runs a heartbeat with 2 retries to determine whether the remote is reachable and
            able to take commands. 2 failures indicates disconnection.

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
            Runs the actual heartbeat command. A successful heartbeat returns "ACK" as a response to 
            the "SYN" message received.

            :return: None
            :rtype: None
        """
        if self.sendRemoteCommand(sentFunction = "heartbeat", sentParameters = {"syn": "SYN"}, logComment = False) != "ACK":
            raise ConnectionRefusedError("Failed heartbeat.")

    def handleDisconnection(self) -> None:
        """
           Returns some of the widgets back to an initial state
           if the disconnection happens. The user should not be able
           to stream or enable actuation on disconnection.

           :return: None
           :rtype: None 
        """
        if self.enableActuationButton.isChecked():
            self.enableActuationButton.setChecked(False)
        
        if self.startStreamPushButton.isChecked():
            self.startStreamPushButton.setChecked(False)
        self.stopDrawing()

        self.isConnected = False
        self.heartbeatTimer.stop()
        self.toggleWidgetsWhenConnected(disabled = True)
        self.mqttClient.loop_stop()
    
    @Slot()
    def checkButtonPress(self) -> None:
        """
            Callback to display that the synchronization trigger has been pressed.
            :return: None
            :rtype: None
        """
        logger.info(redBoldText("Trigger has been pressed."))

    def sendRemoteCommand(self, sentFunction: str, sentParameters: dict[str, Any], logComment: bool = True) -> Any:
        """
            Publishes the command to the remote through MQTT, then waits for a response.

            :param sentFunction: The RPC function that should be executed.
            :type sentFunction: str 
            :param sentParameters: The parameters for the RPC function that should be executed with.
            :type sentParameters: dict[str, Any]
            :param logComment: Whether the remote command should be logged.
            :type logComment: bool
            :return: The return value from the RPC.
            :rtype: Any
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
            The widgets that are enabled on successful connection.

            :param disabled: Whether the widgets should be enabled or disabled.
            :type disabled: bool
            :return: None
            :rtype: None 
        """
        self.configurationBox.setDisabled(disabled)
        self.sessionGroupBox.setDisabled(disabled)
    
    def readControllerConfigurationRemote(self, controlLogicType: ControlLogic, formatForConfiguration: bool) -> dict[str, Any]:
        """
            Reads the configuration from the remote.

            :param controlLogicType: The enum that should be changed.
            :type controlLogicType: ControlLogic
            :param formatForConfiguration: Whether the configuration should be formatted for a save file.
            :type formatForConfiguration: bool
            :return: The configuration parameters from the remote.
            :rtype: dict[str, Any]
        """
        return self.sendRemoteCommand('getConfigurationParameters', {'controlLogicType': controlLogicType, 'formatForConfiguration': formatForConfiguration})

    @Slot()
    def readControllerConfiguration(self) -> None:
        """
            Reads the configuration from the remote then reads it into the GUI fields.

            :return: bool
            :rtype: bool
        """
        controlLogicType = self.graphContexts[self.currentContextIndex].controlLogicType
        zaberConfiguration = self.readControllerConfigurationRemote(controlLogicType, False)
        readConfigurationFromControllerFunc = self.graphContexts[self.currentContextIndex].readConfigurationFromControllerFunc
        readConfigurationFromControllerFunc(self, zaberConfiguration[0])

    @Slot()
    def runCalibration(self) -> None:
        """
            Runs the calibration of the robot to zero the loadcell voltage to the current
            offset value. Subsequent measurements have this offset value subtracted.

            :return: None
            :rtype: None
        """
        self.sendRemoteCommand('calibrateRobot', {})

        if not self.isCalibrated:
            self.isCalibrated = True
            
            # At least one calibration must be performed before streaming and enable torque buttons can be accessed.
            self.enableActuationButton.setEnabled(True)
            self.startStreamPushButton.setEnabled(True)

        logger.info("Calibration has been set.")

    @Slot()
    def changeGraphContext(self, configurationPageIndex: int) -> None:
        """
            Changes the graph context to a different one provided that it exists.
            This should happen when the configuration tab is set to a different control logic tab.

            :param configurationPageIndex: The index of the configuration page that is to be changed into.
            :type configurationPageIndex: int
            :return: None
            :rtype: None
        """
        pageToSwitch = configurationPageIndex if configurationPageIndex < len(self.graphContexts) else 0
        self.plotTabWidget.setCurrentIndex(pageToSwitch)
        self.currentContextIndex = pageToSwitch
        
        # Change logic controller.
        controlLogicType = self.graphContexts[self.currentContextIndex].controlLogicType
        self.sendRemoteCommand('changeControlLogic', {'controlLogicType': controlLogicType})

    def showBottomRowLabel(self, axes: np.ndarray[PlotItem]) -> None:
        """
            Shows the bottom axis (time axis) of the last axis that is displayed on the graph.

            :param axes: A array of PlotItems representing the plots that were generated for this widget.
            :type axes: numpy.ndarray[PlotItem]
            :return: None
            :rtype: None
        """
        # There is a slight pause when showing the time label axis, but it's probably okay.
        def showBottomAxisLabels(plot: PlotItem, show: bool):
            plot.getAxis('bottom').setStyle(showValues = show)
            plot.getAxis('bottom').showLabel(show = show)

        # Look through each column for the last visible plot.
        transposedAxes = np.transpose(axes)
        for plotCols in transposedAxes:
            bottomReached = False
            for plot in reversed(plotCols): 
                if plot.isVisible():
                    if not bottomReached:
                        showBottomAxisLabels(plot, True)
                        bottomReached = True
                    else:
                        showBottomAxisLabels(plot, False)
    
    @Slot()
    def writeChangesToExoController(self) -> None:
        """
            Writes the changes of the current graph context to the remote.
            Changes will only be propagated if validated properly.

            :return: None
            :rtype: None
        """
        currentContext = self.graphContexts[self.currentContextIndex]

        configurationChanges = currentContext.getConfigurationChangesFunc(self)
        if (currentContext.validateConfigurationFunc(configurationChanges)): # & prevents short circuit evaluation.
            currentContext.writeConfigurationChangesFunc(self, configurationChanges)
            logger.info("Changes written to Exoskeleton Controller.")
        else:
            logger.info("Errors found in Configuration. See above for more info.")

    @Slot()
    def warnSixMinuteStream(self) -> None:
        """
            Callback that warns the user that the stream has been run for at least 6 minutes
            with red bolded text in the textbox.

            :return: None
            :rtype: None
        """
        logger.warning(datetime.now().strftime("Stream has been run for 6 minutes at %H:%M:%S."), extra = {TextBrowserHandler.RED_WARN: True})

    def getConfigurationParametersFromGUI(self) -> dict[str, Any]:
        """
            Gets the values from the GUI and places the values into a dictionary. 
            Currently only Spinboxes and Comboboxes are supported

            :return: Dictionary containing the field names and their values.
            :rtype: dict[str, Any]
        """
        def getValueFromElement(field: QWidget) -> int | float:
            if isinstance(field, QAbstractSpinBox):
                return field.value()
            elif isinstance(field, QComboBox):
                return field.currentIndex()
        
        configurationParameters = {}
        for name in [*PrefixNames.configurationWidgetNamePrefixes, *PrefixNames.configurationSingleWidgetNamePrefixes]:
            leftElementField, rightElementField = self.getLegElementsByPrefix(name)

            if self.isLeftLegActive() and leftElementField is not None:
                configurationParameters[leftElementField.objectName()] = getValueFromElement(leftElementField)
            if self.isRightLegActive() and rightElementField is not None:
                configurationParameters[rightElementField.objectName()] = getValueFromElement(rightElementField)
        return configurationParameters
    
    def toggleDisabledConfigurationWidgets(self, disabled: bool) -> None:
        """
            Toggles the configuration of the widgets for the ones that are
            inactive when not connected to the remote.

            :param disabled: Whether the widgets should be disabled or enabled.
            :type disabled: bool
            :return: None
            :rtype: None
        """
        self.readConfigurationButton.setDisabled(disabled)
        self.writeChangesButton.setDisabled(disabled)
        self.setCalibrationButton.setDisabled(disabled)

    def stopDrawing(self) -> None:
        """
            Stops the drawing from the animatedGraphManager (stops taking messages).

            :return: None
            :rtype: None
        """
        self.animatedGraphManager.isStreaming.set()
        self.drawTimer.stop()

    @Slot(bool)
    def toggleStreaming(self, isChecked: bool) -> None:
        """
            Enables the data streaming on the remote. Configuration widgets
            are disabled during this time to prevent unintentional changes.

            :param isChecked: Whether the streaming button has been checked to start streaming.
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

        else:
            self.startStreamPushButton.setText("Start Stream")
            logger.info("Stream has been stopped.")

            self.sendRemoteCommand('stopSend', {}) # Stop streaming on the controller side. Also handles the Trigger streaming
            self.stopDrawing()
            
            # Keep it disabled if the torque button is checked.
            if not self.enableActuationButton.isChecked():
                self.toggleDisabledConfigurationWidgets(disabled = False)

            elapsed_time = time.perf_counter() - self.animatedGraphManager.performanceTimer
            logger.debug(f"FPS: {self.animatedGraphManager.getCounter()/elapsed_time}.")
            self.animatedGraphManager.drawFinalGraph()

    def resetAllGraphLimits(self) -> None:
        """
            Resets all the graphs to specific x and y-axis limits
            given by the graph context's function.

            :return: None
            :rtype: None
        """
        for graphContext in self.graphContexts:
            graphContext.resetGraphLimitsFunc(graphContext.axes, self.MAX_TIME_RANGE)

    @Slot()
    def toggleActuation(self, isChecked: bool) -> None:
        """
            Toggles actuation in the remote to start output movement.
            
            :param isChecked: Whether the "Enable Actuation" button has been checked to start actuation.
            :type isChecked: bool
            :return: None
            :rtype: None
        """
        if isChecked:
            self.enableActuationButton.setText("Disable Actuation")
            logger.info("Actuation has been enabled.")
            self.toggleDisabledConfigurationWidgets(disabled = True)
            self.sendRemoteCommand('enableTorque', {'enable': True})
        else:
            self.enableActuationButton.setText("Enable Actuation")
            logger.info("Actuation has been disabled.")

            # Keep it disabled if the streaming button is checked.
            if not self.startStreamPushButton.isChecked():
                self.toggleDisabledConfigurationWidgets(disabled = False)
            self.sendRemoteCommand('enableTorque', {'enable': False})