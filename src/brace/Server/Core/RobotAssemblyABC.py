from collections.abc import Iterable
import json
import pickle
from string import Template
import time
import traceback
from multiprocessing import Event, Queue

import numpy as np
import pandas as pd
from brace.Server.Core.ComInterface import IInputCom, IOutputCom
from brace.Server.Core.SafetyControl import ISafetyControl
from brace.RealTimeGraphing.Graphing.IDataProducer import IDataProducer
from multiprocessing.synchronize import Condition
from multiprocessing.sharedctypes import Synchronized
from typing import Any, Callable, NamedTuple, override
from brace.Server.Core.RobotABC import RobotABC
from brace.Server.Core.ControlLogic import IControlLogic
from enum import IntEnum
from paho.mqtt import client as mqtt
from collections import deque
from brace.Server.Core.MeasurementLists import IMeasurementLists

import logging
logger = logging.getLogger("logger")
#MAIN
class RobotAssemblyABC(IDataProducer):
    MAX_LEN = 15000
    IGNORED_EXPORT_API_CALLS = { 'heartbeat',  # Removed to keep calls more sparse
                                 'changeControlLogic' } # Handled separately due to different timing to clock step of a normal cycle.
    IGNORED_SIMULATED_API_CALLS = {'enableActuation', 
                                   'calibrateRobots', # Neither these methods have input/output attached during simulation
                                   'restartSharedStartTime', # Avoids restarting the time 
                                   'startSend' } # Avoids having to set up MQTT clients.
    
    @override
    def __init__(self, initialControlLogicType: IntEnum, numRobots: int, controlLogic: dict[IntEnum, Callable[[int], IControlLogic]], 
                 UPDATE_RATE_PER_SECOND: int, startTime: Synchronized = None, robotImplementation: RobotABC = RobotABC, 
                 simulated: bool = False, dataTopicName: str = None, remoteHostTopicTemplate: str = None):
        
        """
        Class that handles overall control between RobotABC objects, reading into the IMeasurementLists, RPC requests, and data export.
        
        :param initialControlLogicType: An initialized enum that represents the control logic object that each RobotABC should be initialized 
        with. This enum should be a member of the controlLogic dictionary also in this __init__. 
        :type initialControlLogicType: IntEnum
        :param numRobots: The number of robots that should be instantiated with this RobotAssemblyABC.
        :type numRobots: int
        :param controlLogic: A dictionary containing anonymous functions that initialize the control logic object that take in an index
        as an indicator for that robot. Should contain the initialControlLogicType IntEnum as a key element.
        :type controlLogic: dict[IntEnum, Callable[[bool], IControlLogic]]
        :param UPDATE_RATE_PER_SECOND: The update rate at which this RobotAssemblyABC should run at. True update rate may fluctuate depending
        on relative load and jitter. 
        :type UPDATE_RATE_PER_SECOND: int
        :param startTime: A relative start time that is bound to one or more IDataProducers to synchronize the exported start time between
        multiple IDataProducer processes. This should be a multiprocessing.Value('d') as times provided by time.perf_counter() are doubles.
        :type startTime: multiprocessing.Value
        :param robotImplementation: The RobotABC implementation that should be homogenously used in this RobotAssemblyABC.
        :type robotImplementation: RobotABC 
        :param simulated: Parameter used for whether or not this object is being used in simulation or online.
        :type simulated: bool
        :param dataTopicName: Name of the topic that should be used for sending data points. Defaults to "datatypes" if none specified.
        :type dataTopicName: str | None
        :param remoteHostTopicTemplate: Topic prefix for the return topic used for server responses back to the client. Should have "$hostname" 
        to distinguish between other possible clients. Defaults to "remotecommands/return/$hostname" if none specified.
        :type remoteHostTopicTemplate: str | None
        """
        
        # Rename if configuration is available.
        if dataTopicName is not None:
            IDataProducer.DATA_TOPIC = dataTopicName
        self.remoteHostTopicTemplate = Template(remoteHostTopicTemplate) if remoteHostTopicTemplate is not None else Template("remotecommands/return/$hostname")

        #declare time vectors: relative time (since computer start), and dt between iterations.
        self.timeAll: deque[float] = deque(maxlen = RobotAssemblyABC.MAX_LEN)
        self.deltaTimeAll: deque[float] = deque(maxlen = RobotAssemblyABC.MAX_LEN)
        
        self.robots: list[RobotABC] = []
        for i in range(numRobots):
            self.robots.append(robotImplementation(controlLogic = controlLogic,
                            debugMode = True,
                            initialControlLogicType = initialControlLogicType,
                            index = i))
        
        self.inferredControlLogicEnumType = type(initialControlLogicType)

        # Events that control the loop in GUI mode.
        self.exit = Event()
        self.sendData = Event()

        self.sendDataEvents = [self.sendData]
        self.apiCallsThisSession: list[tuple[float, str, dict]] = []
        self._tempApiCalls: list[tuple[str, dict]] = []

        # Keep-alive = 0 means no attempt to check for pings. Max is 65335 seconds = 18.2 hours. 
        # 3600 seconds = 1 hour.
        if not simulated:
            self.mqttClient = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
            self.mqttClient.connect("localhost", 8080, keepalive = 3600) 

        self.queuedDataElements = []
        self.maxQueueElements = 3 # Max number of elements that should be stored before publishing.

        super().__init__(UPDATE_RATE_PER_SECOND = UPDATE_RATE_PER_SECOND, startTime = startTime)

    def publishDataToMqtt(self, force: bool = False) -> None:
        """
        Publishes a sequence of NamedTuple elements to the MQTT data topic. Elements are batched to reduce overhead 
        at slight expense of viewing delay. 
        
        :param force: Forces the NameTuple buffer to be published. Such as when controllers change.
        :type force: bool
        :return: None
        :rtype: None
        """
        # Messages are batched, otherwise it seems to affect CAN writes due to apparent overloaded socket spillover.
        # Send when the number of elements is met, or if it was reset in the middle (before elements have been made).
        if force or (len(self.queuedDataElements) == self.maxQueueElements) or (len(self.queuedDataElements) < self.maxQueueElements and not self.sendData.is_set()):
            publishMessage = self.mqttClient.publish(IDataProducer.DATA_TOPIC, pickle.dumps(self.queuedDataElements))
            publishMessage.wait_for_publish()
            self.queuedDataElements.clear()

    def setInputComInterface(self, inputComInterfaces: Iterable[Iterable[IInputCom]]) -> None:
        """
        Initializes the input interfaces that a RobotABC in this RobotAssemblyABC should use.
        
        :param inputComInterfaces: Generally a list of lists containing IInputCom that defines pairwise
        input interfaces to be used for each robot. Each RobotABC is assigned one list of IInputCom from this list of lists.
        :type inputComInterfaces: Iterable[Iterable[IInputCom]]
        :return: None
        :rtype: None
        """
        for i, inputCom in enumerate(inputComInterfaces):
            self.getRobot(index = i).addInputComs(inputCom)

    def setOutputComInterface(self, outputComInterfaces: Iterable[Iterable[IOutputCom]]) -> None:
        """
        Initializes the output interfaces that a RobotABC in this RobotAssemblyABC should use.
        
        :param outputComInterfaces: Generally a list of lists containing IOutputCom that defines pairwise
        input interfaces to be used for each robot. Each RobotABC is assigned one list of IOutputCom from this list of lists.
        :type outputComInterfaces: Iterable[Iterable[IOutputCom]]
        :return: None
        :rtype: None
        """
        for i, outputCom in enumerate(outputComInterfaces):
            self.getRobot(index = i).addOutputComs(outputCom)

    def setMeasurementLists(self, measurementLists: Iterable[IMeasurementLists]) -> None:
        """
        Sets the MeasurementLists that a RobotABC in this RobotAssemblyABC should use.
        
        :param measurementLists: Generally a list of IMeasurementLists subclasses that defines pairwise
        sensor data objects to be used for each robot. Each RobotABC is assigned one IMeasurementList from this list,
        representing the sensor data for that RobotABC.
        :type measurementLists: Iterable[IMeasurementLists]
        :return: None
        :rtype: None
        """
        for i, measurementList in enumerate(measurementLists):
            self.getRobot(index = i).addMeasurementList(measurementList)
    
    def setSafetyControl(self, safetyControls: Iterable[ISafetyControl]) -> None:
        """
        Initializes the ISafetyControl layer that a RobotABC in this RobotAssemblyABC should use.
        
        :param safetyControls: Generally a list of ISafetyControl subclasses that defines the safety
        constraint behavior to be used for each robot. Each RobotABC is assigned one ISafetyControl from this list,
        representing the sensor data for that RobotABC.
        :type measurementLists: Iterable[ISafetyControl]]
        :return: None
        :rtype: None
        """
        for i, safetyControl in enumerate(safetyControls):
            self.getRobot(index = i).addSafetyControls(safetyControl)

    # Exports the data of all robots into a single named tuple.
    def exportRecentData(self, force: bool = False) -> None:
        """
        Creates a NamedTuple object based on the data from the type
        and data from each Control Logic definition. Each field should be defined
        for the NamedTuple which is considered a flat object.

        :param force: Flag to force the data to be published when passed to publishDatatoMqtt
        :type force: bool 
        :return: None
        :rtype: None
        """
        recentData: list[dict[str, float | int]] = []
        exportingDataTypes: set[NamedTuple] = set()

        for robot in self.robots:
            exportingDataType, robotData = robot.exportRobotData()
            exportingDataTypes.add(exportingDataType)
            recentData.append(robotData)
        
        # put data in namedtuple. Both robot should have the same datatype.
        # A set that only has one exporting datatype == same datatype across all robot.
        if len(exportingDataTypes) == 1:
            mergedData = {}
            for data in recentData:
                mergedData = mergedData | data

            exportingDataType = next(iter(exportingDataTypes))
            finalData = exportingDataType(**mergedData, t = self.timeAll[-1] - self.startTime.value)
            self.queuedDataElements.append(finalData)
            self.publishDataToMqtt(force = force)

    def exportNaNData(self, t: float) -> None:
        """ 
        This exports NaNs to the data topic for the current Data type. On graphs, when 
        a NaN is drawn, the points in between the time value and the next valid time value will not plot anything (no line interpolation).
        This is helpful when switching between controllers should not yield valid data in between. 
            
        :param t: The current time relative to the start time for the NaN data point to punctuate the data.
        :type t: float
        :return: None
        :rtype: None
        """
        exportingDataTypes: set[NamedTuple] = set()

        for robot in self.robots:
            if robot.currentControlLogic.DataClass is not None:
                exportingDataTypes.add(robot.currentControlLogic.DataClass)

        if len(exportingDataTypes) == 1:
            dataValues = {}

            exportingDataType = next(iter(exportingDataTypes))
            dataFields = exportingDataType._fields
            for dataField in dataFields:
                dataValues[dataField] = None
            dataValues['t'] = t
            finalData = exportingDataType(**dataValues)
            self.queuedDataElements.append(finalData)
            self.publishDataToMqtt(force = True)

    def setup(self, **kwargs) -> None:
        """
        A setup for things that should be performed before execution, but after the constructor init.

        :params kwargs: Parameters that should be passed to each RobotABC's setup and potentially to control logic objects.
        :type kwargs: dict[str, Any]
        :return: None
        :rtype: None
        """

        # The first cycle is done here (that initializes parameters that would otherwise break in a normal cycle).
        for robot in self.robots:
            robot.setup(**kwargs)
        
        currentTime: float = time.perf_counter()
        self.timeAll.append(currentTime)
        self.deltaTimeAll.append(np.nan) # To align deltaTime with the rest of the arrays, first value is a NaN

    def addSendDataEvent(self, sendData: Synchronized) -> None:
        """
        Binds additional multiprocessing events to be controlled by RobotAssemblyABC (to control when data is sent).

        :param sendData: Event in a while loop to dictate if data should be sent. This is to synchronize when data
        should be sent together with RobotAssemblyABC.
        :type sendData: multiprocessing.Event
        :return: None
        :rtype: None
        """
        self.sendDataEvents.append(sendData)

    def getRobot(self, index: int) -> RobotABC:
        """
        Helper function to retrieve a particular RobotABC indexed by number.

        :param index: Index of the RobotABC within this RobotAssemblyABC.
        :type index: int
        :return: The RobotABC indexed by the number
        :rtype: RobotABC
        """
        return self.robots[index]
    
    """
        The commands below (until remoteCommand) represent the API that can be called 
        using remoteCommand. Calling outside this subset is considered undefined behavior. 
    """

    def calibrateRobots(self) -> None:
        """
        Runs the calibration function in each RobotABC. This is often to zero each robot for relative sensor measurements.

        :return: None
        :rtype: None
        """
        for robot in self.robots:
            robot.setCalibrationOffset()

    def changeControlLogic(self, controlLogicType: IntEnum) -> None:
        """ 
        Changes the logic controllers across all robots, exporting a terminating NaN datapoint if data is being sent. 
        
        :param controlLogicType: An integer enum that corresponds to the control logic from the controller logic
        constructor dictionary, to be changed.
        :type controlLogicType: IntEnum
        :return: None
        :rtype: None
        """
        t = time.perf_counter() - self.startTime.value
        if self.sendData.is_set():
            self.exportNaNData(t)
           
        for robot in self.robots:
            robot.changeControlLogic(controlLogicType = controlLogicType)
        
        self.apiCallsThisSession.append((t, "changeControlLogic", {"controlLogicType" : controlLogicType}))  # Must set this one manually because timestamps will not match up
        logger.debug(f"Change logic controller to {self.inferredControlLogicEnumType(controlLogicType).name}")
    
    def changeControlLogicParameters(self, controlLogicType: IntEnum, parameters: dict[str, float | dict[IntEnum: float]], index: int) -> None:
        """ 
        Requests in-place modification of the control logic parameters. 
        
        :param controlLogicType: An integer enum that corresponds to the control logic to be changed.
        :type controlLogicType: IntEnum
        :param parameters: The parameters that should be overridden (often through setattr, keys can be instance variable names). 
        Parameters are often floats, but may be state lookup tables for torque values.
        :type parameters: dict[str, float | dict[IntEnum: float]]
        :param index: Index of the RobotABC that should undergo the control logic parameter change with respect to this RobotAssemblyABC.
        :type index: int
        :return: None
        :rtype: None
        """
        robot = self.getRobot(index = index)
        robot.changeControlLogicParameters(controlLogicType, parameters)

    def changeMultipleControlLogicParameters(self, controlLogicType: IntEnum, parameters: list[dict[str, float | dict[IntEnum: float]]], index: list[int]) -> None:
        """ Runs the same command as changeControlLogicParameters, except uses index aligned indicies and parameters; 
        used to update in one cycle instead of issuing multiple commands.

        :param controlLogicType: An integer enum that corresponds to the control logic to be changed.
        :type controlLogicType: IntEnum
        :param parameters: A list of parameter dictionaries that should be set for this controlLogicType
        :type parameters: list[dict[str, float | dict[IntEnum: float]]] 
        :param index: A list of indicies corresponding to the robots that are pairwise set to the parameters.
        :type index: list[int]
        :return: None
        :rtype: None
        """
        for index, parameters in zip(index, parameters):
            self.changeControlLogicParameters(controlLogicType, parameters, index)

    def enableActuation(self, enable: bool) -> None:
        """ 
        By default, actuation is turned off and should be enabled through this RPC call. Changes the actuation enable flag for
        each RobotABC object.
        
        :param enable: A flag which determines whether or not output actuation should be performed. If disabled, output calculation
        is still performed, but no outputs are sent out to actuators.
        :type enable: bool
        :return: None
        :rtype: None
        """
        for robot in self.robots:
            robot.enableActuation(enable = enable)

    def getConfigurationParameters(self, controlLogicType: IntEnum, formatForConfiguration: bool) -> tuple[dict[str, float | int], ...]:
        """
        Returns a set of configuration parameters defined by particular control logic. 
        This may be used in two ways: for reading configuration into the GUI, or reading for export into a saved trial file.
        This returns a tuple of configuration parameters (of the same control logic) for each RobotABC that is defined.

        :param controlLogicType: The corresponding IntEnum defined for the control logic that should be exported.
        :type controlLogicType: IntEnum
        :param formatForConfiguration: Flag where True formats should format objects as configuration for saved trial data. False
        should be used for GUI configuration reading.
        :type formatForConfiguration: bool
        :return: Tuple containing configuration parameters for each RobotABC in this RobotAssemblyABC.
        :rtype: tuple[dict[str, float | int], ...]
        """
        configurationParameters = [robot.getConfigurationParameters(controlLogicType, formatForConfiguration) for robot in self.robots]
        return tuple(configurationParameters)

    def heartbeat(self, syn: str) -> str | None:
        """
        Heartbeat pulse to check for alive connections between Client and Server. 
        Returns "ACK" if and only if the initial response is "SYN".
        :param syn: A synchronization string for the heartbeat command.
        :type syn: str
        :return: An acknowledgement string to the synchronization string. None if not "SYN"
        :rtype: str | None
        """
        if syn == "SYN":
            return "ACK"
    
    def restartSharedStartTime(self) -> None:
        """
        Restarts the synchronized start time shared between multiprocesses for data send.
        Datapoints should use this start time as a reference to offset future times with time.perf_counter().
        Saved RPC calls are also cleared such that data trials only contain relevant calls since the restarted time.

        :return: None
        :rtype: None 
        """
        self.setSharedStartTime(updateStartTime = time.perf_counter())
        self.apiCallsThisSession.clear()

    def startSend(self) -> None:
        """
        Sets all bounded Event synchronization flags to start the data streams together.

        :return: None
        :rtype: None
        """
        for sendDataEvent in self.sendDataEvents:
            sendDataEvent.set()

    def stopProcess(self) -> None:
        """
        Stops the RobotAssemblyABC start() loop to cleanly end.

        :return: None
        :rtype: None
        """
        self.exit.set()

    def stopSend(self) -> None:
        """
        Clears bounded send multiprocessing.Event flags to stop the data streams together. 

        :return: None
        :rtype: None
        """
        for sendDataEvent in self.sendDataEvents:
            sendDataEvent.clear()
    
    def exportAPICallEvents(self) -> list[tuple[float, str, dict]]:
        """
        Returns a list of tuples containing the uptime, RPC function name, and parameters that were sent.
        Function names that match names in IGNORED_EXPORT_API_CALLS are not included in this list.

        :return: List of tuples containing RPC calls executed since the last shared start time restart.
        :rtype: list[tuple[float, str, dict]]
        """
        return self.apiCallsThisSession
    
    def turnOnOffControllerRobot(self, index: int, enable: bool) -> bool:
        """
        Enables/Disables the RobotABC from executing control logic and reading sensor data. 
        Disabled RobotABCs still be accessed to retrieve filler NaN data to complete the NameTuple fields, however.

        :params index: Index of the RobotABC to be to be toggled.
        :type index: int
        :params enable: Flag to enable or disable the indexed RobotABC
        :type bool
        :return: Whether or not turning off the RobotABC was successful.
        :rtype: bool
        """
        robot = self.getRobot(index = index)
        return robot.turnOnOffRobot(enable)

    """
        This ends the section of RPC commands that can be run during online execution.
        All other commands should be called in the running script. 
    """

    def remoteCommand(self, functionName: str, argumentParameters: dict[str, Any]) -> Any:
        """
        Runs the RPC command received by the server, calling the function with the given parameters.
        This function will return any return values back to the Client through a separate client topic.

        :params functionName: The RPC function to call.
        :type functionName: str
        :params argumentParameters: A dictionary that contains the parameters to run the function with.
        :type argumentParameters: dict[str, Any]
        :return: Return value of the executed command
        :rtype: Any
        """
        logger.debug(f"Calling {functionName} with parameters {argumentParameters}")
        functionToCall = getattr(self, functionName) # Find the command by name
        returnValue = functionToCall(**argumentParameters) # call the function
        return returnValue # Return whatever it was supposed to return

    @override
    def start(self, timeSynchronizationCondition: Condition = None, **kwargs) -> None:
        """ 
            Starts the RobotAssemblyABC to run the RobotABCs, delegating control to downstream classes as necessary.
            Start times are synchronized and started, setup functions are executed. RPC commands are run, followed by 
            execution of the control loop, followed by data export (when enabled).

            :params timeSynchronizationCondition: Condition that is passed to all IDataProducer start methods. The primary time synchronization 
            reseter notifies the other IDataProducers to continue execution (after waiting). None indicates that no shared condition \
                is assigned between multiple IDataProducers.
            :type timeSynchronizationCondition: multiprocessing.Condition | None
            :params **kwargs: Keyword arguments that are passed through setup functions of RobotABCs and Control Logic objects.
            Necessary kwargs elements are listed below.

            :params sendEnd: Shared queue between producer and consumer. NamedTuple datapoints are added to this queue.
            :type sendEnd: multiprocessing.Queue 

            :return: None
            :rtype: None

        """

        logger.debug('Start')
        sendEnd = kwargs['sendEnd']

        try:

            logger.debug('Paused briefly.')
            #shorten this if possible.
            time.sleep(2)
                
            #start loop
            logger.debug('GO!')
            
            startTime = time.perf_counter()
            self.setSharedStartTime(startTime, timeSynchronizationCondition)

            self.setup(**kwargs)
            while not self.exit.is_set():
                # Perform remote commands at the beginning of each cycle.
                while not sendEnd.empty():
                    clientHostName, receivedCommand, receivedParameters = pickle.loads(sendEnd.get_nowait()) # Format is the name of the function followed by a dictionary of parameters
                    self._tempApiCalls.append((receivedCommand, receivedParameters))
                    returnValue = self.remoteCommand(receivedCommand, receivedParameters)
                    self.mqttClient.publish(topic = self.remoteHostTopicTemplate.substitute(hostname = clientHostName), 
                                            payload = pickle.dumps(returnValue),
                                            qos = 0)

                #keep time for time vectors
                currentTime: float = time.perf_counter()
                self.timeAll.append(currentTime)

                deltaTime: float = self.timeAll[-1] - self.timeAll[-2]
                self.deltaTimeAll.append(deltaTime) # To align deltaTime with the rest of the arrays, first value is a NaN

                currentCycleRobotMeasurements: list[IMeasurementLists] = []
                for robot in self.robots:
                    currentCycleRobotMeasurements.append(robot.runMeasurements(self.deltaTimeAll))
                    
                for robot in self.robots:
                    robot.runCycle(self.timeAll, self.deltaTimeAll, currentCycleRobotMeasurements)

                #put data in namedtuple
                if self.sendData.is_set():
                    self.exportRecentData()
                elif len(self.queuedDataElements) > 0: # Clear the elements if not set to prevent leakage onto next session.
                    self.queuedDataElements.clear()

                # Store API calls for export.
                if self._tempApiCalls:
                    for functionName, functionParameters in self._tempApiCalls:
                        if functionName not in self.IGNORED_EXPORT_API_CALLS:
                            self.apiCallsThisSession.append((self.timeAll[-1] - self.startTime.value, functionName, functionParameters))
                    self._tempApiCalls.clear()

                #pause for short period, but less than timeout, to ensure that the transmit buffer does not become full.
                #otherwise, the code will error out.
                
                # This aligns to the nearest time closest to a multiple of the update time with respect to the start time.
                sleepTime = self.UPDATE_TIME - ((time.perf_counter() - self.startTime.value) % self.UPDATE_TIME) 

                # Then pick either A) Standard sleep.
                if sleepTime > 0:
                    time.sleep(sleepTime)
                
                # or B) Busy waiting loop. Not great on CPU, but this gives more accurate delay.
                # startSleep = time.perf_counter()
                # delay = sleepTime - (time.perf_counter() - startSleep)
                # while(delay > 0):
                #     time.sleep(delay / 10) # Take micronaps? This reduces load a little bit
                #     delay = sleepTime - (time.perf_counter() - startSleep)
            
        except Exception as error:
            logger.debug('Error occurred:')
            traceback.print_exc()
            
        finally:
            logger.debug('Closing Comms.')
            self.mqttClient.disconnect()
             # Close the interface objects to remove error.
            for robot in self.robots:
                robot.turnOnOffRobot(enable = False)

            logger.debug('Script complete.')

    # Function used to retest logic controllers against previously existing data (e.g. from a file).
    # This makes it able to validate the controller without it physically having to put it on again.
    # Any of the API functions may be called in between cycles.
    # Important that the measurements are kept as same (angular velocity is handled in a window, and recalculating it again will change values).
    def simulateControllerData(self, measurementDataFrames: list[pd.DataFrame], eventPipeLine: pd.DataFrame, **kwargs) -> Iterable[NamedTuple]:
        """
        Function used to retest logic controllers against previously existing data (e.g. from a file).
        This makes it able to validate the controller without it physically having to put it on again.
        API functions may be called in between cycles. It is important that the measurements are kept as same
            (recalculating values within a window will change values due to values potentially not being available).
        
        :params measurementDataFrames: A list of pandas Dataframes referencing the data in the IMeasurementLists subclass that should \
        be used in the controller simulation. 
        :type measurementDataFrames: list[pd.DataFrame]
        :params eventPipeLine: A pandas Dataframe listing the uptime, name of the function called, and the parameter (stored as JSON) to be \
        executed before each control iteration. RPC calls that are listed in IGNORED_SIMULATED_API_CALLS are ignored.
        :type eventPipeLine: pd.Dataframe
        :params **kwargs: Other keyword arguments that should be passed to the simulatedSetup of RobotABC and the control logic objects.
        :type **kwargs: dict
        :return: List of NamedTuple datatypes that are exported running new control logic or parameters to be graphed or saved.
        :rtype: Iterable[NamedTuple]
        """
        
        def getRunnableEvents(eventPipeLine: pd.DataFrame, apiEventIndex: int, lastTime: float):
            functionsToRun = []
            index = apiEventIndex
            while index < len(eventPipeLine) and eventPipeLine.loc[index]['uptime'] <= lastTime:
                functionsToRun.append(eventPipeLine.loc[index])
                index += 1
            return index, functionsToRun

        logger.debug('Start')
        dataElements = []

        useableDataFrameWithTimeData = measurementDataFrames[0]
        for dataframe in measurementDataFrames:
            if not dataframe.empty:
                useableDataFrameWithTimeData = dataframe['uptime']
                break

        try:    
            #start loop
            logger.debug('GO!')
            
            # Run setup (things to be run before execution, but after constructor init).
            # The first cycle is done here (that initializes parameters that would otherwise break in a normal cycle).
            self.startTime.value = 0.0

            for robot in self.robots:
                robot.simulatedSetup(**kwargs)
            
            self.timeAll.append(useableDataFrameWithTimeData.iat[0])
            self.deltaTimeAll.append(np.nan) # To align deltaTime with the rest of the arrays, first value is a NaN

            # Run initial event pipeline stuff at the beginning.
            # Keep iterating through the events until the time is after the last timeAll value.
            # changeControlLogic NaN message should skip the NaN message.
            # Need to ignore any of the API commands in IGNORED_SIMULATED_API_CALLS
            eventsIndex = 0
            eventsIndex, toRun = getRunnableEvents(eventPipeLine, eventsIndex, self.timeAll[-1])
            for event in toRun:
                if event['functionName'] not in self.IGNORED_SIMULATED_API_CALLS:
                    self.remoteCommand(event['functionName'], json.loads(event['functionParameters']))
            
            exportingDataTypes: set[NamedTuple] = set()
            for i in range(0, len(useableDataFrameWithTimeData)): # May cause errors in slew.
                # Update the time according to the dataset. But we still need the deltaTime (calculate this).
                # We will have to require execution on the second loop iteration instead of first.
                t = useableDataFrameWithTimeData.iat[i]

                ignoreCycle = False
                eventsIndex, toRun = getRunnableEvents(eventPipeLine, eventsIndex, t)
                for event in toRun:
                    if event['functionName'] not in self.IGNORED_SIMULATED_API_CALLS:
                        # Should just write out the command without adding the NaN data (not actually there).
                        # Skip the copy and runCycle measurement for this NaN. It must match the timeAll[-1], check it first to not add.
                        # changeExoController is a vestigal name, but handle it the same.
                        if event['functionName'] in {'changeExoController', 'changeControlLogic'} and t == event['uptime']:
                            ignoreCycle = True
                            for robot in self.robots:
                                if robot.currentControlLogic.DataClass is not None:
                                    exportingDataTypes.add(robot.currentControlLogic.DataClass)
                        self.remoteCommand(event['functionName'], json.loads(event['functionParameters']))
                
                if not ignoreCycle:
                    self.timeAll.append(t)
                    deltaTime: float = self.timeAll[-1] - self.timeAll[-2]
                    self.deltaTimeAll.append(deltaTime) # To align deltaTime with the rest of the arrays, first value is a NaN

                    # Given an index, just copy the input measurements.
                    currentCycleRobotMeasurements: list[IMeasurementLists] = [] # May be better to not do this every cycle. Just once.
                    for j, robot in enumerate(self.robots):
                        currentCycleRobotMeasurement = robot.copyMeasurements(i, measurementDataFrames[j])
                        currentCycleRobotMeasurements.append(currentCycleRobotMeasurement)
                                
                    for robot in self.robots:
                        robot.runCycle(self.timeAll, self.deltaTimeAll, currentCycleRobotMeasurements)

                    # Have to be able to send the data somewhere else. Maybe just return the data?
                    recentData: list[dict[str, float | int]] = []
                    exportingDataTypes: set[NamedTuple] = set()

                    for robot in self.robots:
                        exportingDataType, robotData = robot.exportRobotData()
                        exportingDataTypes.add(exportingDataType)
                        recentData.append(robotData)
                    
                    # put data in namedtuple. Both robots should have the same datatype.
                    # A set that only has one exporting datatype == same datatype across all robots.
                    if len(exportingDataTypes) == 1:
                        mergedData = {}
                        for data in recentData:
                            mergedData = mergedData | data

                        exportingDataType = next(iter(exportingDataTypes))
                        finalData = exportingDataType(**mergedData, t = self.timeAll[-1] - self.startTime.value)
                else:
                    exportingDataTypes: set[NamedTuple] = set()
                    for robot in self.robots:
                        if robot.currentControlLogic.DataClass is not None:
                            exportingDataTypes.add(robot.currentControlLogic.DataClass)
                    
                    if len(exportingDataTypes) == 1:
                        dataValues = {}
                        exportingDataType = next(iter(exportingDataTypes))
                        dataFields = exportingDataType._fields
                        for dataField in dataFields:
                            dataValues[dataField] = None
                        dataValues['t'] = self.timeAll[-1] - self.startTime.value
                        finalData = exportingDataType(**dataValues)
                    exportingDataTypes.clear()
                dataElements.append(finalData)
        except Exception as error:
            logger.debug('Error occurred:')
            traceback.print_exc()
        finally:
            logger.debug('Ending processing of simulated results.')
        return dataElements