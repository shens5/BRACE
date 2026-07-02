from __future__ import annotations
from brace.example.exoskeleton.ControlLogicLookup import ControlLogicEnum
from brace.UI.ConfigurationGrid import ConfigurationGrid
import brace.UI.example.GUIController.PrefixNames as PrefixNames
import brace.UI.GUIController.UIConfigurationHelpers as UIConfigurationHelpers
from brace.UI.LoggingHelpers import redBoldText, joinStringsWithSpace
from typing import TYPE_CHECKING, Any
from PySide6.QtWidgets import QWidget

from brace.UI.example.PlotConfiguration import ConfiguredStandingPlots
if TYPE_CHECKING:
    from brace.UI.example.MainWindow import MainWindow
import logging
logger = logging.getLogger("logger")

configurationNameLabelPrefixes = ['standingLegLabel']

changeableThresholds = ['turnOffThreshold',
                        'turnOnThreshold']

configurationWidgetLookup = {
    'standingMode': 'standingModeComboBox',
    'standingTorque': 'standingTorqueDoubleSpinBox',
    'slewRate': 'standingRampRateSpinBox',
    'turnOffThreshold': 'standingTurnOffThresholdSpinBox',
    'turnOnThreshold': 'standingTurnOnThresholdSpinBox'
}

configurationWidgetPrefixes = list(configurationWidgetLookup.values())

def getStandingConfigurationChanges(configurationObjects: dict[str, QWidget], configurationGrid: ConfigurationGrid) -> tuple[dict[str, Any], dict[str, Any]]:
    """
        Gets the configuration from the GUI box divided between left and right legs for standing.

        :params configurationObjects: dictionary containing the QWidgets referenced by name.
        :type configurationObjects: dict[str, QWidget]
        :params configurationGrid: The configuration box object in the GUI.
        :type configurationGrid: ConfigurationGrid

        :return: Tuple of configuration widgets that were assigned for the legs. 
        :rtype: tuple[dict[str, Any], dict[str, Any]]
    """
    leftConfigurationChanges, rightConfigurationChanges = UIConfigurationHelpers.getConfigurationChanges(configurationObjects, configurationWidgetLookup)
    leftConfigurationChanges['standingMode'] = leftConfigurationChanges['standingMode'] == 'Enabled' # Change these to booleans.
    rightConfigurationChanges['standingMode'] = rightConfigurationChanges['standingMode'] == 'Enabled'
    return leftConfigurationChanges, rightConfigurationChanges

def _setStandingPlotThresholdValues(parent: MainWindow, turnOffThreshold: int, turnOnThreshold: int, isLeft: bool) -> None:
    standingGraphContext = parent.graphContexts[parent.standingGraphContextIndex]
    ConfiguredStandingPlots.StandingPlotsPyQt.setThresholdValues(standingGraphContext.axes, turnOffThreshold, turnOnThreshold, isLeft)

def readStandingConfigurationFromController(parent: MainWindow, configuration: dict[str, Any], isLeft: bool) -> None:
    """
        Read the standing configuration from the controller remote into the GUI fields.

        :params parent: The MainWindow GUI whose configuration should be changed.
        :type parent: MainWindow
        :params configuration: The configuration from the remote that the fields should be changed into.
        :type configuration: dict[str, Any]
        :params isLeft: Whether or not the fields belong to the left or right legs.
        :type isLeft: bool

        :return: None
        :rtype: None
    """
    replacementTable = {configurationWidgetName: configuration[keyword] for keyword, configurationWidgetName in configurationWidgetLookup.items()}
    for configurationObjectName, configurationObjectValue in replacementTable.items():
        if configurationObjectName == 'standingModeComboBox':
            configurationObjectValue = 0 if configurationObjectValue else 1 # 0 is enabled, 1 is disabled.
            parent.configurationObjects[PrefixNames.formatConfigurationWidgetLeg(configurationObjectName, isLeft)].setCurrentIndex(configurationObjectValue)
        else:
            parent.configurationObjects[PrefixNames.formatConfigurationWidgetLeg(configurationObjectName, isLeft)].setValue(configurationObjectValue)
    
    _setStandingPlotThresholdValues(parent, **{thresholdName: configuration[thresholdName] for thresholdName in changeableThresholds}, isLeft = isLeft)
    logger.info(f"Read Standing configuration from controller on {PrefixNames.getLegSideLong(isLeft)} leg.")

def readStandingConfigurationFromSaveFile(configurationObjects: dict[str, QWidget], configuration: dict[str, Any], isLeft: bool) -> None:
    """
        Read the configuration for the standing controller from the saved configuration file into the Standing Configuration GUI fields.

        :params configurationObjects: A dictionary containing the widgets, referenced by keyword name.
        :type configurationObjects: dict[str, QWidget]
        :params configuration: The values from the configuration file that should be changed into.
        :type configuration: dict[str, Any]
        :params isLeft: Whether or not the fields belong to the left or right legs.
        :type isLeft: bool

        :return: None
        :rtype: None
    """
    replacementTable = {configurationWidgetName: configuration[keyword] for keyword, configurationWidgetName in configurationWidgetLookup.items()}
    for configurationObjectName, configurationObjectValue in replacementTable.items():
        if configurationObjectName == 'standingModeComboBox':
            configurationObjectValue = 0 if configurationObjectValue else 1 # 0 is enabled, 1 is disabled.
            configurationObjects[PrefixNames.formatConfigurationWidgetLeg(configurationObjectName, isLeft)].setCurrentIndex(configurationObjectValue)
        else:
            configurationObjects[PrefixNames.formatConfigurationWidgetLeg(configurationObjectName, isLeft)].setValue(configurationObjectValue)

def validateStandingConfiguration(configurationBox: ConfigurationGrid, legActive: bool, isLeft: bool, configuration: dict[str, Any]) -> bool:
    """
        Validates the configuration for the standing controller GUI fields. Returns True if valid and false otherwise.

        :params configurationBox: The GUI box containing the fields.
        :type configurationBox: ConfigurationGrid
        :params legActive: Whether or not this leg is active or not (to be checked).
        :type legActive: bool
        :params isLeft: Whether or not the left or right leg should be checked.
        :type isLeft: bool
        :params configuration: The configuration to be checked.
        :type dict[str, Any]

        :return: Whether or the configuration set is valid.
        :rtype: bool
    """
    turnOnThreshold = configuration['turnOnThreshold']
    turnOffThreshold = configuration['turnOffThreshold']

    legSide = PrefixNames.getLegSideLong(isLeft = isLeft)
    passedValidationChecks = True

    if legActive:
        if turnOnThreshold <= turnOffThreshold:
            logger.warning(redBoldText(joinStringsWithSpace(f"{legSide} Turn-Off Threshold is greater than Turn-on threshold.", 
                                                f"Please check values in Standing > Turn-On Threshold and Turn-Off Thresholds ({legSide}).",
                                    f"Current Values are Turn-off Threshold: {turnOffThreshold}, Turn-On Threshold: {turnOnThreshold}")))
            passedValidationChecks = False
    return passedValidationChecks

def writeStandingConfigurationChanges(parent: MainWindow, leftConfigurationChanges: dict[str, Any], rightConfigurationChanges: dict[str, Any]) -> None:
    """
        Writes the configuration changes from the client to the remote.

        :params parent: The MainWindow object that is calling this function.
        :type parent: MainWindow
        :params leftConfigurationChanges: The configuration changes that should be written, belonging to the left leg.
        :type dict[str, Any]
        :params rightConfigurationChanges: The configuration changes that should be written, belonging to the right leg.
        :type dict[str, Any]

        :return: None
        :rtype: None
    """
    if parent.isLeftLegActive():
        parent.sendRemoteCommand('changeControlLogicParameters', {'controlLogicType': ControlLogicEnum.STANDING, 'parameters': leftConfigurationChanges, 'index': PrefixNames.getLeftRightIndex(True)})
    if parent.isRightLegActive():
        parent.sendRemoteCommand('changeControlLogicParameters', {'controlLogicType': ControlLogicEnum.STANDING, 'parameters': rightConfigurationChanges, 'index': PrefixNames.getLeftRightIndex(False)})

def adjustStandingPlotThresholdValues(parent: MainWindow, leftConfigurationChanges: dict[str, Any], rightConfigurationChanges: dict[str, Any]) -> None:
    """
        Adjusts the threshold values for the standing plots

        :params parent: The MainWindow object that is calling this function.
        :type parent: MainWindow
        :params leftConfigurationChanges: The configuration changes belonging to the left leg for the threshold values.
        :type dict[str, Any]
        :params rightConfigurationChanges: The configuration changes belonging to the left leg for the threshold values.
        :type dict[str, Any]

        :return: None
        :rtype: None
    """
    if parent.isLeftLegActive():
        _setStandingPlotThresholdValues(parent, **{thresholdName: leftConfigurationChanges[thresholdName] for thresholdName in changeableThresholds}, isLeft = True)
    if parent.isRightLegActive():
        _setStandingPlotThresholdValues(parent, **{thresholdName: rightConfigurationChanges[thresholdName] for thresholdName in changeableThresholds}, isLeft = False)