from multiprocessing.sharedctypes import Synchronized
from typing import override
from brace.Server.Core.ComInterface import IInputCom, IOutputCom
import logging
from multiprocessing import Queue
from multiprocessing.synchronize import Event

logger = logging.getLogger("logger")

class CANInterface2(IInputCom, IOutputCom):
    """
        The CAN input and output interface written for the Bionic Power Agilik actuators.
        This is used as both input and output, hence the multiple inheritance. This interface
        reads in the shared memory variables to get the measurements that are constantly read
        asynchronously on a separate CAN reading process for parallelization. It additionally writes
        any output CAN messages out to a queue that is read by the same CAN reading process
        to write actuator commands.
    """
    def __init__(self, channel: int, canReaderQueue: Queue, kneeAngle: Synchronized, fsr: Synchronized, canEnable: Event) -> None:
        """
            :param channel: The channel designated for this CAN bus line (left is 1, right is 0).
            :type channel: int
            :param canReaderQueue: The queue that funnels CAN messages to the process.
            :type canReaderQueue: multiprocessing.Queue
            :param kneeAngle: Floating point shared memory for reading knee angle values.
            :type kneeAngle: multiprocessing.Value
            :param fsr: Floating point shared memory for reading FSR values.
            :type fsr: multiprocessing.Value
            :param canEnable: Event that starts up CAN processing reading and writing.
            :type canEnable: multiprocessing.Event
            :return: None
            :rtype: None
        """
        self.canOn = False
        self.channel = channel
        self.canReaderQueue = canReaderQueue
        self.kneeAngle = kneeAngle
        self.fsr = fsr
        self.canEnable = canEnable

    @override
    def isComOn(self) -> bool:
        """
            Returns whether this interface is enabled (active).
            
            :return: Whether or not the interface is on.
            :rtype: bool
        """
        return self.canOn

    # multiprocessing.Value types come with their own write locks to prevent data races.
    def printEncoder(self) -> float:
        """
            Gets the knee angle value at this point in time, locking as necessary.
            
            :return: Sampled knee angle value
            :rtype: float
        """
        return float(self.kneeAngle.value)

    def printFSR(self) -> float:
        """
            Gets the FSR value at this point in time, locking as necessary.
            
            :return: Sampled FSR value
            :rtype: float
        """
        return float(self.fsr.value)
    
    @override
    def turnOnOffComm(self, enable: bool) -> bool:
        """
            Turns the communications interface as necessary for the communications.
            The flags for the process are also set and reset such that the CAN process does not
            asynchronously run.

            :param enable: Whether the communications should be enabled or disabled.
            :type enable: bool
            :return: True (supposed to be successful or not)
            :rtype: bool
        """
        if not self.canOn and enable: # Only change when there is a difference in enabled state.
            self.canOn = enable
            self.canEnable.set()
            logger.debug(f"CAN Interfacing with Process (on): CAN{self.channel}")
        elif self.canOn and not enable:
            self.canOn = False
            self.canEnable.clear()
            logger.debug(f"CAN Interfacing with Process (off): CAN{self.channel}") # Probably was successful.
        return True
    
    @override
    def sendOutput(self, outputMsgData: bytes) -> None:
        """
            Writes the output messages to the CAN processing queue for
            output actuation. Only written if the interface is active.

            :param outputMsgData: The CAN message to write to the actuator.
            :type outputMsgData: bytes
            :return: None
            :rtype: None
        """
        if self.canOn:
            self.canReaderQueue.put(outputMsgData, block = False)