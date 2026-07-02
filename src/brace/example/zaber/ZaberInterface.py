
from typing import override
from zaber_motion.ascii.device import Device
from zaber_motion.units import Units
from zaber_motion.ascii import Axis, Connection
from brace.Server.Core.ComInterface import IInputCom, IOutputCom
import logging
logger = logging.getLogger("logger")

class ZaberInterface(IInputCom, IOutputCom):
    """
        The input and output nterface that reads input and writes output to the Zaber X-MCC.
    """
    def __init__(self, serialPort: str, axisNum: int):
        """
            :param serialPort: The serial port for read and write connected to this device.
            :type serialPort: str
            :param axisNum: The axis number, used if there are multiple axes allowed on the X-MCC.
            :type axisNum: int
        """
        super().__init__()
        self.serialOn = False
        self.axisNum = axisNum
        self.comPort = serialPort
        self.serialConnection: Connection = Connection.open_serial_port(self.comPort)
        self.actuator: Device = self.serialConnection.detect_devices()[0]
        self.axis: Axis = self.actuator.get_axis(self.axisNum)
        self.axis.home()
        
    @override
    def isComOn(self) -> bool:
        """
            Returns whether or not this serial interface is enabled or disabled.

            :return: Whether the serial interface is active.
            :rtype: bool
        """
        return self.serialOn
    
    def printPosition(self) -> float | None:
        """
            Gets the position of the actuator in millimeters as a sensor input.

            :return: The current actuator position for this axis.
            :rtype: float
        """
        position = self.axis.get_position(unit = Units.LENGTH_MILLIMETRES)
        return position

    @override
    def turnOnOffComm(self, enable: bool) -> bool:
        """
            Enable or disables this interface during usage.

            :param enable: Enables the device communication if true, disables if false.
            :type enable: bool
            :return: Whether or not this communication was successfully enabled or disabled.
            :rtype: bool
        """
        if not self.serialOn and enable: # Only change when there is a difference in enabled state.
            self.serialOn = True
            logger.debug(f"Zaber Serial turning on {self.comPort}")
        elif self.serialOn and not enable:
            self.serialOn = False
            logger.debug("Zaber Serial turning off")
        else:
            return True # No changes whatsoever = good.

        # Certified good change of state.
        self.serialOn = enable
        return True
    
    @override
    def sendOutput(self, position: float) -> None:
        """
            Moves the position of the actuator in absolute values. This does not wait for the 
            actuator to reach the final position before the next cycle is performed.

            :param position: The position after checks that should be input to the actuator.
            :type position: float
            :return: None
            :rtype: None 
        """ 
        if self.serialOn:
            self.axis.move_absolute(position, wait_until_idle = False, unit = Units.LENGTH_MILLIMETRES)