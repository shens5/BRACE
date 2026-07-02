from abc import abstractmethod
from typing import override

class UnexpectedInitializationError(BaseException):
    """ 
        Raised for issues when turnOnOffComm is attempted for turn on, but does not work. 
    """

class IComInterface():
    """ 
        Generic interface for communications (both input and output) in relation to this framework. 
    """

    @abstractmethod
    def isComOn(self) -> bool:
        """
            Returns a bool on whether the communication interface is active (and ready to send commands).
            
            :return: bool representing active communication interface.
            :rtype: bool
        """
        pass

    @abstractmethod
    def turnOnOffComm(self, enable: bool) -> bool:
        """
            Activates or deactivates this communication interface. Returns bool on whether or not it succeeded.
            
            :param enable: True if interface should be active. False otherwise.
            :type enable: bool
            :return: Bool on whether or not a successful change of "active/inactive" has been made.
            :rtype: bool
        """
        pass

class IInputCom(IComInterface):
    """ 
        Input Communications Interface. No methods are listed as it is the responsibility of the
        subclass to determine sensors (and how they relate to IMeasurementLists, which a list of these IInputComs).
        Up to the subclass to figure out what methods it needs to print out (and how it connects with the IMeasurementLists) 
    """
    pass

class IOutputCom(IComInterface):
    """ 
        Output Communications interface responsible for handling how output is directed toward actuators or 
        other device.
    """
    @abstractmethod
    def sendOutput(self, outputMsgData: bytes) -> None:
        """
            Sends commands to the output communications interface. outputMsgData is paired against the iterable containing
            IOutputComs. 
            
            :param outputMsgData: The command to send to the output communications interface. 
                Note that this is a single value sent to the output communication.
            :type outputMsgData: bytes
            :return: None
            :rtype: None
        """
        pass

class NullCom(IInputCom, IOutputCom):
    """ Empty class that is used in the simulation for input and output communications. """

    @override
    def isComOn(self) -> bool:
        return False

    @override
    def turnOnOffComm(self, enable: bool) -> bool:
        return True
    
    @override
    def sendOutput(self, outputMsgData: bytes) -> None:
        pass