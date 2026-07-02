from brace.Server.Core.RobotAssemblyABC import RobotAssemblyABC

class ExoController(RobotAssemblyABC):
    """
        This class is a subclass of the stock defined RobotAssemblyABC. Custom RPC functions
        can be written to execute changes during runtime.
    """
    def setControllerLegExtensionPositive(self, index: int, isExtensionPositive: bool) -> None:
        """
            :param index: The index of the robot in the ExoController that should be changed.
            :type index: int
            :param isExtensionPositive: Whether extension should be considered positive, else flexion is positive.
            :type isExtensionPositive: bool
            :return: None
            :rtype: None
        """
        exoLeg = self.getRobot(index = index)
        exoLeg.setExtActuationConvention(extTorquePositive = isExtensionPositive)