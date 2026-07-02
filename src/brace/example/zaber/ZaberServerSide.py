from multiprocessing import Condition, Process, RLock, freeze_support, Queue
import sys
import logging
import os

from brace.example.exoskeleton.ExoLeg import ExoLeg
from brace.example.exoskeleton.ExoController import ExoController
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from datetime import datetime
import atexit
from brace.Server.Core.RemoteProcedureCallHandler import RemoteProcedureCallHandler
import brace.example.zaber.ZaberControlLogic as Zaber
from brace.example.zaber.ZaberInterface import ZaberInterface
from brace.example.zaber.ZaberMeasurementList import ZaberMeasurementLists
from brace.example.zaber.ZaberTransform import ZaberTransform
from brace.example.zaber.ArduinoADCInterface import LoadCellInterface
from serial.tools import list_ports
from bidict import bidict
from brace.Server.Core.ControlLogic import IControlLogic
from brace.Server.GPIOSynch.PushButton import ButtonPress

# To log uncaught exceptions.
def handleException(excType, excValue, excTraceback):
    if issubclass(excType, KeyboardInterrupt):
        sys.__excepthook__(excType, excValue, excTraceback)
        return

    logger.error("Uncaught exception", exc_info = (excType, excValue, excTraceback))
        
# This should be a factory method that builds out default parameter logic controllers.
def createControlLogics() -> dict[Zaber.ControlLogic, IControlLogic]:
    """
        Factory method for the control logic, creating a lambda that takes in the index
        for the single control law defined for this case.

        :return: A dictionary containing the enum and the control logic defined.
        :rtype: dict[Zaber.ControlLogic, IControlLogic]
    """
    zaberControlLogic = lambda index: Zaber.ZaberControlLogic(index = index)
    return { Zaber.ControlLogic.ZaberController: zaberControlLogic }

def query_com() -> bidict[str, str]:
    """
        Generates dictionary of available serial ports and their description

        :return: Dictionary of available serial ports and descriptions
        :rtype: dict[str, str]
    """
    port_info = sorted(list_ports.comports())
    return bidict({port: desc for port, desc, _ in port_info})
    
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

    atexit.register(lambda: logger.debug(f"Session ended at {datetime.now().strftime("%Y/%m/%d %H:%M:%S.%f")}"))

    multiprocessingQueue = Queue()
    remoteProcedureHandler = RemoteProcedureCallHandler()

    timeSynchronizationLock = RLock()
    timeSynchronizationCondition = Condition(timeSynchronizationLock)

    comInfo = query_com()
    xMCCCom = comInfo.inv["X-MCC2"]
    unoR4Minima = comInfo.inv["UNO R4 Minima - CDC Port"]
    
    logger.debug("Starting ExoController process.")
    leftInputCom = [ZaberInterface(xMCCCom, 2), LoadCellInterface(unoR4Minima)]

    leftOutputCom = leftInputCom[:1]

    leftMeasurementList = ZaberMeasurementLists()

    leftSafetyCheck = ZaberTransform(invert = False) #nm

    controllerProducer = ExoController(initialControlLogicType = Zaber.ControlLogic.ZaberController,
                                       numRobots = 1,
                                       controlLogic = createControlLogics(), 
                                       UPDATE_RATE_PER_SECOND = 300,
                                       robotImplementation = ExoLeg)
    controllerProducer.setInputComInterface([leftInputCom])
    controllerProducer.setOutputComInterface([leftOutputCom])
    controllerProducer.setMeasurementLists([leftMeasurementList])
    controllerProducer.setSafetyControl([leftSafetyCheck])

    rpcHandlerProcess = Process(target = remoteProcedureHandler.start, args = (multiprocessingQueue,), daemon = True)
    hasButton = True
    if hasButton:
        logger.debug("Starting Trigger process.")
        buttonProducer = ButtonPress(buttonPin = 24, UPDATE_RATE_PER_SECOND = 100, startTime = controllerProducer.getSharedStartTime())
        buttonProcess = Process(target = buttonProducer.start, args = (timeSynchronizationCondition,), daemon = True)
        controllerProducer.addSendDataEvent(buttonProducer.sendData) # The controller handles when button sends data (previous attempts at a manager to handle both in a separate process) yielded slow GUI.
        buttonProcess.start()
        atexit.register(buttonProducer.stopProcess)

    rpcHandlerProcess.start()
    atexit.register(multiprocessingQueue.close)
    atexit.register(controllerProducer.stopProcess)
    print("Done... Ready to serve!")

    # Running Zaber's libraries on a different process causes weird deadlocks.
    # Thus, we are forced to use the main process to run the control loop. 
    controllerProducer.start(timeSynchronizationCondition, kwargs = {'sendQueue': multiprocessingQueue})

if __name__ == '__main__':

    freeze_support()
    logger = logging.getLogger("logger")
    main()