import asyncio
from multiprocessing.sharedctypes import Synchronized
import os
import signal
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
import can
import brace.example.exoskeleton.BionicPowerActuatorProcess.CanHelpers as CanHelpers
from multiprocessing import Process, Queue, Value, Event
import multiprocessing
import time
from queue import Empty
from multiprocessing.synchronize import Event as SynchronizedEvent

def forceCurrentDeadZone(commandCurrent: float) -> float:
    return 0.0 if -20 <= commandCurrent <= 20 else commandCurrent  # ma

def torqueToCurrent(desTorque: float) -> float:
    # input: Nm
    # output: mA
    commandCurrent = (desTorque*0.3936 + 0.0154)*1000
    return commandCurrent

def convertTorqueConventionSign(extTorquePositive: bool, torqueIn: float) -> float:
    return -torqueIn if extTorquePositive else torqueIn
class CANReader():
    def __init__(self, channel: int) -> None:
        """ This is a separate implementation in attempt to read from the CAN from a separate process.
        Then to read the CAN data, it would just either read from shared memory buffer or push data through a queue (probably the former; less latency).
        This is all a way to decrease the latency from reading from CAN.

        A separate child process that sets up the CAN sockets and everything. 
        Whenever there is an actual read from the CAN based on the 280 id, then it should continue to read. Should store these values, multiprocess locking them.
        It should just be able to read from shared memory for the knee angle and FSR data and sends the torque message (fire and forget). 
        The whole point of this is to reduce the amount of I/O time and also to address the issue where we have to read at least twice in order for the torque 
        to be stable for some reason (something about the CAN timing and arbitration, not sure. On firmware side of the actuator).
        
        :param channel: The CAN bus channel that should be read.
        :type channel: int
        """
        self.can: can.BusABC = None
        self.channel = channel
        self.bitRate = 100000
        self.buffSize = 65536
        self.stopEvent: SynchronizedEvent
        self.canEnable: SynchronizedEvent

    def readCANMessage(msg: can.Message) -> tuple[float, float]:
        """
            Parses a CAN bus message for a tuple of knee angle and FSR values.

            :param msg: CAN bus message to be parsed. Should have the id 280.
            :type: can.Message
            :return: Tuple of knee angle and FSR values.
            :type: tuple[float, float]
        """
        #encoderFlexPositive - true if positive angle readings mean flexion (1884)
        #based on printSensors1/2
        if msg is not None and msg.arbitration_id == 280:
            #8th byte shifted 
            dec4 = (msg.data[7] << 8) | msg.data[6]
            if dec4 < 32768: #max of signed 16-bit
                #4096 = 13-bit
                #360 degrees
                #angle = (int(dec4) * 360.0)/4096
                angle = (int(dec4) * 180/3.14159)/4096
            else:
                angle = -((int(0xFFFF - dec4) * 180/3.14159)/4096)
            # There's no real consistency on where it is since it is FSR dependent
            # dec2 -> toe, dec3 -> mid, dec1 -> heel => BPO9166 SN: 12975 (Left)
            # dec2 -> toe, dec1 -> mid, dec3 -> heel => BPO8042 SN: 10425 (Right)
            dec1 = (msg.data[1] << 8) | msg.data[0] # Change endianness
            force1 = int(dec1) / (2 ** 16 - 1) * 3000
            dec2 = (msg.data[3] << 8) | msg.data[2]
            force2 = int(dec2) / (2 ** 16 - 1) * 3000
            dec3 = (msg.data[5] << 8) | msg.data[4]
            force3 = int(dec3) / (2 ** 16 - 1) * 3000
            Force_CanX = force1 + force2 + force3

            # Depending on the motor, extension on torque is positive, and flexion on encoder is negative. Or vice versa.
            # But encoder convention and torque convention are two different things. All of the encoders are flexion negative (extension positive).
            # encoderAngle = -angle if encoderFlexPositive else angle
            encoderAngle = -angle
            return encoderAngle, Force_CanX
        return None

    async def readMessage(self, kneeAngle: Synchronized, fsr: Synchronized, canEnable: SynchronizedEvent) -> None:
        """
        Coroutine that reads messages continuously through the CAN AsyncBufferedReader object. Messages are parsed
        into two shared memory variables (with locks), which are read by a corresponding IInputObject class.

        :param kneeAngle: Shared memory variable that represents the knee angle.
        :type kneeAngle: multiprocessing.Value (double)
        :param fsr: Shared memory variable that represents the FSR value.
        :type fsr: multiprocessing.Value (double)
        :param canEnable: Event that indicates that the CAN reading should be started.
        :type canEnable: multiprocessing.Event
        :return: None
        :rtype: None
        """
        reader = can.AsyncBufferedReader()
        notifier = can.Notifier(self.can, [reader], loop = self.loop)   
        while not self.stopEvent.is_set():
            if canEnable.wait(timeout = 10):
                try:
                    message = await reader.get_message()
                    if message is not None:
                        parsed = CANReader.readCANMessage(message)
                        if parsed is not None:
                            kneeAngle.value, fsr.value = parsed
                except asyncio.CancelledError:
                    pass
        notifier.stop()

    async def writeTorque(self, queue: Queue, canEnable: SynchronizedEvent) -> None:
        """
        Coroutine writes the torque using messages added by IOutputCom for this CANReader channel. "Sentinel" messages
        indicate that the loop should be stopped.

        :param queue: Queue shared with a corresponding IOutputCom that writes torque messages. This is used by this
        CANReader object to write the needed torque value to the actuator.
        :type queue: multiprocessing.Queue
        :param canEnable: An Event that waits until enabled to start reading queued messages. This enable is set by
        the corresponding IOutputCom object.
        :type canEnable: multiprocessing.Event
        :return: None
        :rtype: None
        """
        while not self.stopEvent.is_set():
            if canEnable.wait(timeout = 10):
                try:
                    # run blocking queue.get in thread
                    item = await asyncio.to_thread(queue.get, 10)
                    if item == "Sentinel":
                        break
                    else:
                        CanHelpers.sendTorqueCmd_v2(self.can, item)
                except Empty:
                    # Empty queue from queue.get, just keep going.
                    pass
                except Exception:
                    # protect against queue closed / other exceptions
                    break

    async def start(self, stopEnable: SynchronizedEvent, queue: Queue, kneeAngle: Synchronized, fsr: Synchronized, canEnable: SynchronizedEvent) -> None:
        """
        Coroutine that initializes the CAN bus channels, then creates the running loop, reading CAN bus messages and 
        writingTorque from the multiprocessing queue.

        :param stopEnable: An event to stop the process to leave the reading loop.
        :type stopEnable: multiprocessing.Event
        :param queue: A queue that canReader reads from to write torque commands.
        :type queue: multiprocessing.Queue
        :param kneeAngle: A shared memory variable for the knee angle that is read by the IInputCom object to gather knee angle
        data.
        :type kneeAngle: multiprocessing.Value (double)
        :param fsr: A shared memory variable for the FSR voltage that is read by the IInputCom object to get FSR data.
        :type fsr: multiprocessing.Value (double)
        :param canEnable: An event to start reading and writing to this CAN bus.
        :type canEnable: multiprocessing.Event
        :return: None
        :rtype: None
        """

        CanHelpers.OS_CloseCAN(self.channel)
        CanHelpers.setBitRate(self.channel, self.bitRate)
        CanHelpers.setTransQueue(self.channel, self.buffSize)
        CanHelpers.OS_OpenCAN(self.channel)

        self.canEnable = canEnable
        self.stopEvent = stopEnable
        self.queue = queue

        self.can = CanHelpers.openSocket(self.channel)

        self.loop = asyncio.get_running_loop()
        # create both tasks and await them concurrently; when one returns (e.g. sentinel)
        self.task = asyncio.gather(
            self.readMessage(kneeAngle, fsr, self.canEnable),
            self.writeTorque(queue, self.canEnable),
        )
        try:
            await self.task
        except asyncio.exceptions.CancelledError:
            pass
        finally:
            self.shutdownHandler(None, None)

    def shutdownHandler(self, _signum, _frame) -> None:
        """
            Handles normal clean up if SIGTERM or SIGINT were received.
        """
        # SIGTERM/SIGINT handler
        self.stopEvent.set()
        self.canEnable.clear()
        if self.can:
            CanHelpers.stopTorqueCmd(self.can)
            CanHelpers.closeSocket(self.can)
            self.can = None
        CanHelpers.OS_CloseCAN(self.channel)

def createCANPrimitives(channel: int) -> tuple[CANReader, SynchronizedEvent, SynchronizedEvent, Queue, Synchronized, Synchronized]:
    """
        Factory method that creates a tuple of events, queues, and shared memory values for a given channel.

        :params channel: The channel that the CAN bus should read from (0 or 1, in a 2-channel system).
        :type channel: int
        :return: A tuple of CANReader, events, queues, and shared memory variables for the corresponding IInputCom implementation
        to use.
        :rtype: tuple[CANReader, multiprocessing.Event, multiprocessing.Event, multiprocessing.Queue, 
        multiprocessing.Value (double), multiprocessing.Value (double)]
    """
    canReader = CANReader(channel=channel)
    stopEnable = Event()
    canEnable = Event()
    queue = Queue()
    kneeAngle = Value('d', 0.0)
    fsr = Value('d', 0.0)
    return canReader, stopEnable, canEnable, queue, kneeAngle, fsr

def runMultiCAN(canReader: CANReader, stopEnable: SynchronizedEvent, queue: Queue,
                kneeAngle: Synchronized, fsr: Synchronized, canEnable: SynchronizedEvent) -> None:
    """
        Runs the CAN Bus in a separate process, running asynchronously, using a separate queue
        to handle write messages and an asynchronous reader to get CAN bus messages when available.

        :param canReader: Object that designates the reader object for a particular channel.
        :type canReader: CANReader
        :param stopEnable: An event to stop the process to leave the reading loop.
        :type stopEnable: multiprocessing.Event
        :param queue: A queue that canReader reads from to write torque commands.
        :type queue: multiprocessing.Queue
        :param kneeAngle: A shared memory variable for the knee angle that is read by the IInputCom object to gather knee angle
        data.
        :type kneeAngle: multiprocessing.Value (double)
        :param fsr: A shared memory variable for the FSR voltage that is read by the IInputCom object to get FSR data.
        :type fsr: multiprocessing.Value (double)
        :param canEnable: An event to start reading and writing to this CAN bus.
        :type canEnable: multiprocessing.Event
        :return: None
        :rtype: None
    """
    # Detach child process from parent's process group = no terminal signals.
    try:
        os.setpgrp()
        devnull_fd = os.open(os.devnull, os.O_RDWR) 
        os.dup2(devnull_fd, 0)   # stdin -> /dev/null. This solves not being able to Ctrl-C the terminal. 
        # optional: close the extra fd if different
        if devnull_fd > 2:
            os.close(devnull_fd)

        # restore SIGINT to default to avoid child's custom handler interfering
        signal.signal(signal.SIGTERM, canReader.shutdownHandler)
        signal.signal(signal.SIGINT, signal.SIG_DFL)

        # run the asyncio event loop
        asyncio.run(canReader.start(stopEnable, queue, kneeAngle, fsr, canEnable))
    except Exception:
        # setpgrp probably doesn't work on windows
        pass
    finally:
        canReader.shutdownHandler(None, None)

if __name__ == "__main__":
    # force spawn to avoid inheriting parent's event loop which cause deadlocks on exit
    multiprocessing.set_start_method('spawn', force = True)

    canReader1, stopEnable1, canEnable1, queue1, kneeAngle1, fsr1 = createCANPrimitives(channel = 1)
    canEnable1.set()

    canReader0, stopEnable0, canEnable0, queue0, kneeAngle0, fsr0 = createCANPrimitives(channel = 0)
    # canEnable1.set()

    # make process non-daemonic so we can join/terminate it cleanly
    multiprocessedItem1 = Process(target = runMultiCAN,
                                  args = (canReader1, stopEnable1, queue1, kneeAngle1, fsr1, canEnable1),
                                  daemon = False)
    multiprocessedItem1.start()

    multiprocessedItem0 = Process(target = runMultiCAN,
                                  args = (canReader0, stopEnable0, queue0, kneeAngle0, fsr0, canEnable0),
                                  daemon = False)
    multiprocessedItem0.start()

    try:
        for i in range(1000):
            torque = 0
            queue1.put(CanHelpers.getTorqueMsgData_v2(convertTorqueConventionSign(True, torqueToCurrent(torque))))
            # queue0.put(CanHelpers.getTorqueMsgData_v2(convertTorqueConventionSign(True, torqueToCurrent(torque))))
            # print(f"Ang: {float(kneeAngle1.value):.2f} == FSR: {float(fsr1.value):.2f}")
            time.sleep(0.005)
    except KeyboardInterrupt:
        # Parent intercepted Ctrl-C: perform graceful shutdown
        print("KeyboardInterrupt: shutting down child process...")

    finally:
        # Graceful shutdown sequence
        # Tell child to stop reading/writing
        stopEnable1.set()
        canEnable1.clear()

        stopEnable0.set()
        canEnable0.clear()

        queue1.put("Sentinel")
        queue0.put("Sentinel")

        time.sleep(1.0) # Wait for the queue to clear out. Probably would be better to use a proper Condition variable.

        queue1.close()
        queue0.close()

        queue1.join_thread()
        queue0.join_thread()

        multiprocessedItem1.join(timeout = 5.0)
        if multiprocessedItem1.is_alive():
            print("Child 1 did not exit in time; terminating.")
            multiprocessedItem1.terminate()
            multiprocessedItem1.join(timeout = 2.0)

        multiprocessedItem0.join(timeout = 5.0)
        if multiprocessedItem0.is_alive():
            print("Child 0 did not exit in time; terminating.")
            multiprocessedItem0.terminate()
            multiprocessedItem0.join(timeout = 2.0)
        print("Shutdown complete.")