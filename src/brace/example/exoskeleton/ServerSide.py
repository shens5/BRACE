from multiprocessing import Condition, Process, RLock, freeze_support, Queue
import sys
import logging
import os
from datetime import datetime
import time
import numpy as np
from brace.example.exoskeleton.BionicPowerActuatorProcess.CANReader import createCANPrimitives, runMultiCAN
from brace.example.exoskeleton.CANInterface2 import CANInterface2
from brace.example.exoskeleton.ExoLeg import ExoLeg
from brace.example.exoskeleton.ExoController import ExoController
from brace.Server.Core.RemoteProcedureCallHandler import RemoteProcedureCallHandler
from brace.example.exoskeleton.ExoMeasurementList import MeasurementLists
from brace.example.exoskeleton.SlewSafetyChecks import SlewSafetyChecks
from brace.example.exoskeleton.ControlLogicLookup import ControlLogicEnum
from brace.Server.GPIOSynch.PushButton import ButtonPress
from brace.example.exoskeleton.ControlLogic.ControlLogicDefaults import createControlLogics
from brace.UI.GUIController.InitializationFunctions import loadInitFile, getDefaultsDictionary, getSettingsDictionary

# To log uncaught exceptions.
def handleException(excType, excValue, excTraceback):
    if issubclass(excType, KeyboardInterrupt):
        sys.__excepthook__(excType, excValue, excTraceback)
        return

    logger.error("Uncaught exception", exc_info = (excType, excValue, excTraceback))
        
def main():
    print("Starting Server...")
    logger.setLevel(logging.DEBUG)  # Logger debug has to be set to the "lowest" level

    fileFormatter = logging.Formatter(fmt = "%(asctime)s.%(msecs)03d %(levelname)s, [%(pathname)s, %(filename)s, %(module)s, %(funcName)s, %(lineno)d]: %(message)s", 
                                  datefmt = "%Y-%m-%d %H:%M:%S")
    dirPath = os.path.dirname(os.path.realpath(__file__))   
    logsPath = os.path.join(dirPath, "logs")
    os.makedirs(logsPath, exist_ok = True)
    logFileName = os.path.join(logsPath, datetime.now().strftime("%Y%m%d_%H%M%S_Controller.log"))
    fileHandler = logging.FileHandler(logFileName)
    fileHandler.setLevel(logging.DEBUG)
    fileHandler.setFormatter(fileFormatter)
    logger.addHandler(fileHandler)

    sys.excepthook = handleException
    scriptDirectory = os.path.dirname(os.path.abspath(__file__))
    initFileConfiguration = loadInitFile(os.path.join(scriptDirectory, "ExoskeletonControl.ini"))
    initDefaults = getDefaultsDictionary(initFileConfiguration)
    initSettings = getSettingsDictionary(initFileConfiguration)

    logger.debug("Starting ExoController process.")
    remoteProcedureHandler = RemoteProcedureCallHandler(initSettings.get('commandTopic', None))

    # Two CAN reader/writer (left and right) are run in different processes for parallelism.
    canReaderProcess1 = Process(target = runMultiCAN,
                                  args = (canReader1, stopEnable1, canQueue1, kneeAngle1, fsr1, canEnable1),
                                  daemon = True)
    
    canReaderProcess0 = Process(target = runMultiCAN,
                                  args = (canReader0, stopEnable0, canQueue0, kneeAngle0, fsr0, canEnable0),
                                  daemon = True)
    canReaderProcess1.start()
    canReaderProcess0.start()

    # Layers that are created for the exoskeleton. CANInterface2 is the input/output interface for the knee angle, FSR/Actuator combo.4
    # Multiple interfaces should be placed in the list if there are multiple sensors to be used.
    leftCom = [CANInterface2(channel = 1, canReaderQueue = canQueue1, kneeAngle = kneeAngle1, fsr = fsr1, canEnable = canEnable1)]
    rightCom = [CANInterface2(channel = 0, canReaderQueue = canQueue0, kneeAngle = kneeAngle0, fsr = fsr0, canEnable = canEnable0)]

    # Layer that handles all of the sensor data and any desired recording of output data internally for control iterations.
    leftMeasurementList = MeasurementLists()
    rightMeasurementList = MeasurementLists()

    # Layer that handles all of the safety checks for both actuators. These tend to be more hardcoded maximum parameters.
    leftSafetyCheck = SlewSafetyChecks(extTorquePositive = True, 
                                       MAX_SLEW_RATE = 80, #nm/s
                                       MAX_EXT_TORQUE = 13, #nm
                                       MAX_FLEX_TORQUE = -13) #nm
    
    rightSafetyCheck = SlewSafetyChecks(extTorquePositive = True, 
                                       MAX_SLEW_RATE = 80, #nm/s
                                       MAX_EXT_TORQUE = 13, #nm
                                       MAX_FLEX_TORQUE = -13) #nm

    # This is the main class that runs the execution of all of the robots, initializing with the FSM5 control logic.
    controllerProducer = ExoController(initialControlLogicType = ControlLogicEnum.FSM5,
                                       numRobots = 2, 
                                       controlLogic = createControlLogics(initDefaults),
                                       UPDATE_RATE_PER_SECOND = 500,
                                       robotImplementation = ExoLeg,
                                       dataTopicName = initSettings.get('dataTopicName', None),
                                       remoteHostTopicTemplate = initSettings.get('remoteHostTopic', None))
    
    # Set up all the layers. These are zipped to the robots that were created in ExoController. Run as a separate process.
    controllerProducer.setInputComInterface(np.array([leftCom, rightCom]))
    controllerProducer.setOutputComInterface(np.array([leftCom, rightCom]))
    controllerProducer.setMeasurementLists(np.array([leftMeasurementList, rightMeasurementList]))
    controllerProducer.setSafetyControl(np.array([leftSafetyCheck, rightSafetyCheck]))
    producerProcess = Process(target = controllerProducer.start, args = (timeSynchronizationCondition,), kwargs= {'sendEnd': multiprocessingQueue}, daemon = True)

    # The button is created as a separate process that generates data to the data topic. Initialized to pin 24, at 100 Hz.
    hasButton = initSettings.get('hasTrigger', True)
    if hasButton:
        logger.debug("Starting Trigger process.")
        buttonProducer = ButtonPress(buttonPin = 24, UPDATE_RATE_PER_SECOND = 100, startTime = controllerProducer.getSharedStartTime(), 
                                     triggerTopicName = initSettings.get('triggerTopicName', None))
        buttonProcess = Process(target = buttonProducer.start, args = (timeSynchronizationCondition,), daemon = True)
        controllerProducer.addSendDataEvent(buttonProducer.sendData) # The controller handles when button sends data (previous attempts at a manager to handle both in a separate process) yielded slow GUI.
        buttonProcess.start()

    producerProcess.start()
    print("Done... Ready to serve!")

    try:
        # The main process starts the remote procedure handling. This reads in the messages into the queue to be read for the ExoController.
        remoteProcedureHandler.start(multiprocessingQueue = multiprocessingQueue)
    except KeyboardInterrupt:
        # Parent intercepted Ctrl-C: perform graceful shutdown
        print("KeyboardInterrupt: shutting down child process...")
        logger.debug("KeyboardInterrupt: shutting down child process...")
    finally:
        # Graceful shutdown sequence
        # Tell child to stop reading/writing
        multiprocessingQueue.close()
        controllerProducer.stopProcess()
        
        if hasButton:
            buttonProducer.stopProcess()
 
        stopEnable1.set()
        canEnable1.clear()

        stopEnable0.set()
        canEnable0.clear()

        canQueue1.put("Sentinel")
        canQueue0.put("Sentinel")

        time.sleep(1.0) # Wait for the queue to clear out. Probably would be better to use a proper Condition variable.

        canQueue1.close()
        canQueue0.close()

        canReaderProcess1.join(timeout = 5.0)
        if canReaderProcess1.is_alive():
            logger.error("Child 1 did not exit in time; terminating.")
            canReaderProcess1.terminate()

        canReaderProcess0.join(timeout = 5.0)
        if canReaderProcess0.is_alive():
            logger.error("Child 0 did not exit in time; terminating.")
            canReaderProcess0.terminate()

        logger.info(f"Shutdown complete. Session ended at {datetime.now().strftime("%Y/%m/%d %H:%M:%S.%f")}")

if __name__ == '__main__':
    freeze_support()
    logger = logging.getLogger("logger")

    # Create the locking primitives that are shared between the CAN processes and the interfaces.
    canReader1, stopEnable1, canEnable1, canQueue1, kneeAngle1, fsr1 = createCANPrimitives(channel = 1)
    canReader0, stopEnable0, canEnable0, canQueue0, kneeAngle0, fsr0 = createCANPrimitives(channel = 0)
    multiprocessingQueue = Queue()
    multiprocessingQueue.cancel_join_thread()
    canQueue0.cancel_join_thread()
    canQueue1.cancel_join_thread()
    timeSynchronizationLock = RLock()
    timeSynchronizationCondition = Condition(timeSynchronizationLock)
    main()