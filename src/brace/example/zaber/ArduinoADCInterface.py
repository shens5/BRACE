from typing import override
from brace.Server.Core.ComInterface import IInputCom, UnexpectedInitializationError
import serial
import logging
logger = logging.getLogger("logger")

class LoadCellInterface(IInputCom):
    """
        This class is the input interface for the Arduino that
        gets the load cell voltage from the Serial interface.
    """
    def __init__(self, serialPort: str):
        """
            :param serialPort: The serial port that the Arduino is connected to.
            :type serialPort: str
        """
        super().__init__()
        self.serialOn = False
        self.comPort = serialPort
        self.baudrate = 115200
        self.serialConnection = serial.Serial(self.comPort, baudrate = self.baudrate)
        if not self.serialConnection.readable():
            raise UnexpectedInitializationError()

    @override
    def isComOn(self) -> bool:
        """
            Returns whether or not this communications interface is considered on.

            :return: Whether this communication is on.
            :rtype: bool
        """
        return self.serialOn
    
    def readValue(self, ser: serial.Serial) -> float:
        """
            Gets the one channel voltage from the Arduino by serial command.
            
            :param serial: The Serial class that is communicating through USB.
            :type serial: serial.Serial
            :return: The voltage value read from the Arduino ADC.
            :rtype: float
        """
        ser.write("\n".encode('utf-8')) # Creates the command.
        receivedLine = ser.readline()
        # voltage0, voltage1 = receivedLine.decode('utf-8').split(",")
        # return float(voltage0), float(voltage1) # In dual mode.
        return float(receivedLine.decode('utf-8'))
    
    def printLoadCellValue(self) -> float:
        """
            Gets the load cell voltage by parsing in the Serial message
            
            :return: The floating-point voltage read in by the Arduino.
            :rtype: float
        """
        return self.readValue(self.serialConnection)

    @override
    def turnOnOffComm(self, enable: bool) -> bool:
        """
            Enables and disables the state of this interface.

            :param enable: Enables or disables this serial interface
            :type enable: bool
            :return: Whether or not enabling or disable was successful.
            :rtype: bool
        """
        if not self.serialOn and enable: # Only change when there is a difference in enabled state.
            logger.debug(f"Arduino Serial turning on {self.comPort}") 
        elif self.serialOn and not enable:
            logger.debug("Arduino Serial turning off") # Probably was successful.
        else:
            return True # No changes whatsoever = good.

        # Certified good change of state.
        self.serialOn = enable
        return True