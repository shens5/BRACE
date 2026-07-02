import os
import can
import struct

#FUNCTIONS
#CAN communication set-up
def setBitRate(ChNum: int, bRate: int) -> None:
    """
        Sets the bit rate for the CAN bus socket.

        :param ChNum: The channel number of the CAN bus
        :type ChNum: int
        :param bRate: The rate that should be set
        :type bRate: int
        :return: None
        :rtype: None
    """
    os.system('sudo ip link set can' + str(ChNum) + ' type can bitrate ' + str(bRate))

def setTransQueue(ChNum: int, Buffer: int) -> None:
    """
        Sets the transmit queue length for this CAN bus socket.

        :param ChNum: The channel number of the CAN bus
        :type ChNum: int
        :param Buffer: The size of the CAN bus buffer
        :type Buffer: int
        :return: None
        :rtype: None
    """
    os.system('sudo ifconfig can' + str(ChNum) + ' txqueuelen ' + str(Buffer))

def OS_OpenCAN(ChNum: int) -> None:
    """
        Opens the CAN socket.

        :param ChNum: The channel number of the CAN bus.
        :type ChNum: int
        :return: None
        :rtype: None
    """
    os.system('sudo ifconfig can' + str(ChNum) + ' up')

def OS_CloseCAN(ChNum: int) -> None:
    """
        Closes the CAN socket

        :param ChNum: The channel number of the CAN bus
        :type ChNum: int
        :return: None
        :rtype: None
    """
    os.system('sudo ifconfig can' + str(ChNum) + ' down')

def openSocket(ChNum: int) -> can.interface.BusABC:
    """
        Opens the CAN bus interface using a ThreadSafeBus, filtering out for only the id 280 message that contains
        the knee encoder and FSR sensor data. Two versions are given for the legacy Raspberry Pi that used and one for the
        updated version.

        :param ChNum: The channel number of the CAN socket that should be opened.
        :type ChNum: int
        :return: The BusABC object that interfaces with the OS CAN socket.
        :rtype: can.interface.BusABC
    """
    if can.__version__ == '4.5.0': # New version on second Pi
        canFilters = [{'can_id': 0x118, 'can_mask': 0x7FF, 'extended': False}] # Only get the id 280 message which has encoder and sensor data.
        canX = can.ThreadSafeBus(channel = 'can' + str(ChNum), interface = 'socketcan', can_filters = canFilters)
    elif can.__version__ == '3.3.4': # Old legacy version on first Pi
        canX = can.ThreadSafeBus(channel = 'can' + str(ChNum), bustype = 'socketcan')
    return canX

def testSocket(canX: can.interface.BusABC) -> bool:
    """
        Checks whether the socket initialization has been successful using a short receive command.

        :param canX: The python CAN interface used to receive CAN messages.
        :type canX: can.interface.BusABC
        :return: Whether the socket is available (by constantly read messages)
        :rtype: bool 
    """
    return canX.recv(1.0) is not None # Shorter test to check if CAN is working

def closeSocket(canX: can.interface.BusABC) -> None:
    """ 
        Closes the Python CAN interface for the channel.
    """
    canX.shutdown()

def printEncoder(canX: can.interface.BusABC) -> float | None:
    """
        Parses the CAN values from the received CAN message.
        Only the id 280 represents a proper sensor message. There are other 
        messages that are on the CAN bus for current draw, but these are filtered
        out at the Python CAN interface level. None means that the message was not
        read properly.

        :param canX: The Python CAN interface for reading CAN messages
        :type canX: can.interface.BusABC
        :return: The encoder value after conversion in degrees.
        :rtype: float | None  
    """
    #encoderFlexPositive - true if positive angle readings mean flexion (1884)

    #based on printSensors1/2
    msg = canX.recv(10.0)
    if msg is not None and msg.arbitration_id == 280:
        #8th byte shifted 
        dec4 = (msg.data[7] << 8) | msg.data[6]
        if dec4 < 32768: #max of signed 16-bit
            #4096 = 13-bit
            #360 degrees
            #angle = (int(dec4) * 360.0)/4096
            angle = (int(dec4) * 180/3.14159)/4096
        else :
            #angle = -((int(0xFFFF - dec4) * 360.0)/4096)
            angle = -((int(0xFFFF - dec4) * 180/3.14159)/4096)
            #print('else occurred in print encoder')

        # Depending on the motor, extension on torque is positive, and flexion on encoder is negative. Or vice versa.
        # But encoder convention and torque convention are two different things. All of the encoders are flexion negative (extension positive).
        # encoderAngle = -angle if encoderFlexPositive else angle
        encoderAngle = -angle
        return encoderAngle
    # else :
    #     print(f"Check encoder messaging setup. Arbitration ID: {msg.arbitration_id}")
    #     return None
    
def printFSR(canX: can.interface.BusABC) -> float | None:
    """
        Parses the CAN values from the received CAN message.
        Only the id 280 represents a proper sensor message. There are other 
        messages that are on the CAN bus for current draw, but these are filtered
        out at the Python CAN interface level. None means that the message was not
        read properly.

        :param canX: The Python CAN interface for reading CAN messages
        :type canX: can.interface.BusABC
        :return: The FSR value after conversion in degrees.
        :rtype: float | None  
    """
    fsr = canX.recv(10.0)

    # There's no real consistency on where it is since it is FSR dependent
    # dec2 -> toe, dec3 -> mid, dec1 -> heel => BPO9166 SN: 12975 (Left)
    # dec2 -> toe, dec1 -> mid, dec3 -> heel => BPO8042 SN: 10425 (Right)
    if fsr.arbitration_id == 280:
        dec1 = (fsr.data[1] << 8) | fsr.data[0] # Change endianness
        force1 = int(dec1) / (2 ** 16 - 1) * 3000
        dec2 = (fsr.data[3] << 8) | fsr.data[2]
        force2 = int(dec2) / (2 ** 16 - 1) * 3000
        dec3 = (fsr.data[5] << 8) | fsr.data[4]
        force3 = int(dec3) / (2 ** 16 - 1) * 3000
        Force_CanX = force1 + force2 + force3
        return Force_CanX
    else:
        return None
        
def getTorqueMsgData_v2(currentInput: float) -> bytes:
    """
        Creates a torque message that is sent to the actuator
        from the amount of current.

        :param currentInput: Converted torque to current value to be
        used by the actuator.
        :type currentInput: float
        :return: The CAN message (in bytes) that is sent through the CAN wire for
        actuation.
        :rtype: bytes
    """
    currentInput = int(currentInput)
    #signed-int 16-bit little endian
    torqueMsgData = struct.pack('<h',currentInput)
    return torqueMsgData

def sendTorqueCmd_v2(canX: can.interface.BusABC, torqueMsgData: bytes) -> None:
    """
        Sends the torque message out through the CAN bus socket with the 0x112 id.

        :param canX: The Python CAN interface for reading CAN messages
        :type canX: can.interface.BusABC
        :param torqueMsgData: The data message that should be sent for writing to the actuator.
        :type torqueMsgData: bytes:
        :return: None
        :rtype: None
    """
    if can.__version__ == '4.5.0': # New version on second Pi
        msg = can.Message(arbitration_id=0x112, data=[1, torqueMsgData[0],torqueMsgData[1]],is_extended_id=False)
    elif can.__version__ == '3.3.4': # Old legacy version on first Pi
        msg = can.Message(arbitration_id=0x112, data=[1, torqueMsgData[0],torqueMsgData[1]],extended_id=False)
    canX.send(msg)

def stopTorqueCmd(canX: can.interface.BusABC) -> None:
    """
        Sends a stop message through the CAN bus socket with the 0x110 (priority over all other messages).
        There is no payload associated with this message and torque is stopped if there are no messages 
        for 200 ms.
        :param canX: The Python CAN interface for reading CAN messages
        :type canX: can.interface.BusABC
        :return: None
        :rtype: None 
    """
    if can.__version__ == '4.5.0': # New version on second Pi
        msg = can.Message(arbitration_id = 0x110, data = None, is_extended_id=False)
    elif can.__version__ == '3.3.4': # Old legacy version on first Pi
        msg = can.Message(arbitration_id = 0x110, data = None , extended_id=False)
    canX.send(msg)