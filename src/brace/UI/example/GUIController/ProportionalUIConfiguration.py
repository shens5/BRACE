from __future__ import annotations
from brace.example.exoskeleton.ControlLogicLookup import ControlLogicEnum
from brace.UI.ConfigurationGrid import ConfigurationGrid
import brace.UI.example.GUIController.PrefixNames as PrefixNames
import brace.UI.GUIController.UIConfigurationHelpers as UIConfigurationHelpers
from PySide6.QtWidgets import QWidget
from brace.UI.LoggingHelpers import redBoldText, joinStringsWithSpace
from typing import TYPE_CHECKING, Any
if TYPE_CHECKING:
    from brace.UI.example.MainWindow import MainWindow
import logging
logger = logging.getLogger("logger")

configurationNameLabelPrefixes = ['proportionalAngleLimitsLegLabel',
                                  'proportionalTorqueLegLabel']

configurationWidgetLookup = {'thetaMin': 'proportionalMinAngleLimitSpinBox',
                             'thetaMax': 'proportionalMaxAngleLimitSpinBox',
                             'minTorque': 'proportionalMinTorqueDoubleSpinBox',
                             'maxTorque': 'proportionalMaxTorqueDoubleSpinBox' }

configurationWidgetPrefixes = list(configurationWidgetLookup.values())

def getProportionalConfigurationChanges(configurationObjects: dict[str, QWidget], configurationGrid: ConfigurationGrid) -> tuple[dict[str, Any], dict[str, Any]]:
    """
        Gets the configuration for the proportional controller from the GUI box divided by left and right.

        :params configurationObjects: A dictionary containing the name of the object and the widget object created.
        :type configurationObjects: dict[str, QWidget]
        :params configurationGrid: Configuration Grid object that contains all of the fields.
        :type configurationGrid: configurationGrid

        :return: Tuple of the fields and their values.
        :rtype: tuple[dict[str, Any]]
    """
    leftConfigurationChanges, rightConfigurationChanges = UIConfigurationHelpers.getConfigurationChanges(configurationObjects, configurationWidgetLookup)
    return leftConfigurationChanges, rightConfigurationChanges

def readProportionalConfigurationFromController(parent: MainWindow, configuration: dict[str, Any], isLeft: bool) -> None:
    """
        Reads the proportional configuration values from the controller into the GUI fields.

        :params parent: The main window for the GUI.
        :type parent: MainWindow
        :params configuration: The configuration from the remote controller formatted by key and value pair.
        :type configuration: dict[str, Any]
        :params isLeft: Whether or not the the configuration to be set belongs to the left or right leg.
        :type isLeft: bool

        :return: None
        :rtype: None
    """
    for configurationObjectKeyword, configurationObjectName in configurationWidgetLookup.items():
        configurationObjectValue = configuration[configurationObjectKeyword]
        parent.configurationObjects[PrefixNames.formatConfigurationWidgetLeg(configurationObjectName, isLeft)].setValue(configurationObjectValue)
    logger.info(f"Read Proportional configuration from controller on {PrefixNames.getLegSideLong(isLeft)} leg.")

def readProportionalConfigurationFromSaveFile(configurationObjects: dict[str, QWidget], configuration: dict[str, float | dict], isLeft: bool) -> None:
    """
        Reads the configuration from the saved configuration file into the GUI fields.

        :params configurationObjects: dictionary of QWidgets that can be referenced by their name.
        :type configurationObjects: dict[str, QWidget]
        :params configuration: dictionary of string and the configuration values as given by the saved configuration file. The string names should match
        the field names that are in configurationObjects.
        :type configuration: dict[str, float | dict]
        :params isLeft: Whether or not the configuration to be set belongs to the left or right leg.
        :type isLeft: bool

        :return: None
        :rtype: None
    """
    for configurationObjectKeyword, configurationObjectName in configurationWidgetLookup.items():
        configurationObjectValue = configuration[configurationObjectKeyword]
        configurationObjects[PrefixNames.formatConfigurationWidgetLeg(configurationObjectName, isLeft)].setValue(configurationObjectValue)


def adjustProportionalPlotThresholdValues(_: MainWindow, __: dict[str, Any], ___: dict[str, Any]) -> None:
    """
        Placeholder that does nothing because proportional has no threshold values on any of the graphs.
    """
    pass

def validateProportionalConfiguration(configurationBox: ConfigurationGrid, legActive: bool, isLeft: bool, configuration: dict[str, Any]) -> bool:
    """
        Validates the configuration fields in the proportional controller. Return True if valid configuration and False otherwise.

        :params configurationBox: The configuration grid in the GUI whose values should be validated.
        :type configurationBox: ConfigurationGrid
        :params legActive: Boolean that determines whether or not the parameters should be checked (leg may be disabled).
        :type legActive: bool
        :params isLeft: Whether or not the leg to be checked is left.
        :type isLeft: bool
        :params configuration: The configuration that was received and should be validated.
        :type configuration: dict[str, Any]
        
        :return: Whether or not the changed configuration was valid.
        :rtype: bool
    """
    
    thetaMin, thetaMax, minTorque, maxTorque = tuple([configuration[keyword] for keyword in configurationWidgetLookup.keys()])

    legSide = PrefixNames.getLegSideLong(isLeft = isLeft)
    passedValidationChecks = True

    if legActive:
        if thetaMax <= thetaMin:
            logger.warning(redBoldText(joinStringsWithSpace(f"{legSide} Minimum Angle is greater than or equal to Maximum Angle.", 
                                                f"Please check values in Proportional > Angle Limits > Minimum Angle Limit and Maximum Angle Limit ({legSide}).",
                                    f"Current Values are Minimum Angle Limit: {thetaMin}, Maximum Angle Limit: {thetaMax}")))
            passedValidationChecks = False
        
        if maxTorque <= minTorque:
            logger.warning(redBoldText(joinStringsWithSpace(f"{legSide} Minimum Torque is greater than or equal to Maximum Torque.",
                                    f"Please check values in Proportional > Torque > Minimum Torque and Maximum Torque ({legSide}). ",
                            f"Current Values are Minimum Torque: {minTorque}, Maximum Torque: {maxTorque}")))
            passedValidationChecks = False
    return passedValidationChecks

def writeProportionalConfigurationChanges(parent: MainWindow, leftConfigurationChanges: dict[str, Any], rightConfigurationChanges: dict[str, Any]) -> None:
    """
        Writes the changes to the remote from the proportional controller.

        :params parent: The main window for the GUI.
        :type parent: MainWindow
        :params leftConfigurationChanges: Left configuration changes to be passed to the remote.
        :type leftConfigurationChanges: dict[str, Any]
        :params rightConfigurationChanges: Right configuration changes to be passed to the remote.
        :return: None
        :rtype: None 
    """
    if parent.isLeftLegActive():
        parent.sendRemoteCommand('changeControlLogicParameters', {'controlLogicType': ControlLogicEnum.PROPORTIONAL, 'parameters': leftConfigurationChanges, 'index': PrefixNames.getLeftRightIndex(True)})
    if parent.isRightLegActive():
        parent.sendRemoteCommand('changeControlLogicParameters', {'controlLogicType': ControlLogicEnum.PROPORTIONAL, 'parameters': rightConfigurationChanges, 'index': PrefixNames.getLeftRightIndex(False)})