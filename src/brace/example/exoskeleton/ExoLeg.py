from brace.Server.Core.RobotABC import RobotABC

class ExoLeg(RobotABC):
    """
        This class is a subclass of the stock defined RobotABC. Custom RPC functions
        should be designed to forward function calls that may be received from the RobotAssemblyABC
        subclass.
    """
    def setExtActuationConvention(self, extTorquePositive: bool) -> None:
        """
            RPC function that sets the torque convention of the actuator in the ISafetyControl layer.
            
            :param extTorquePositive: Whether extension should defined as positive torque.
            :type extTorquePositive: bool
            :return: None
            :rtype: None
        """
        self.safetyControl.setExtActuationConvention(extTorquePositive)