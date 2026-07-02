from __future__ import annotations
from brace.example.zaber.ZaberControlLogic import ControlLogic
from brace.UI.LoggingHelpers import redBoldText, joinStringsWithSpace
from typing import TYPE_CHECKING, Any
if TYPE_CHECKING:
    from brace.example.zaber.MainWindow import ZaberMainWindow
from bidict import bidict
import logging
logger = logging.getLogger("logger")

attributeWidgetLookup = bidict({
    'positionMin': 'proportionalMinPositionLimitDoubleSpinBox',
    'positionMax': 'proportionalMaxPositionLimitDoubleSpinBox',
    'loadcellMin': 'proportionalMinLoadCellDoubleSpinBox',
    'loadcellMax': 'proportionalMaxLoadCellDoubleSpinBox'
})

def getProportionalConfigurationChanges(parent: ZaberMainWindow) -> dict[str, Any]:
    """
        Gets the configuration in the GUI for this controller.

        :param parent: The main GUI where this function is being called.
        :type parent: ZaberMainWindow
        :return: Dictionary containing the configuration values.
        :rtype: dict[str, Any]
    """
    configurationWidgetLookup = {} 
    for attribute, widgetName in attributeWidgetLookup.items():
        configurationWidgetLookup[attribute] = getattr(parent, widgetName).value()
    return configurationWidgetLookup

def readProportionalConfigurationFromController(parent: ZaberMainWindow, configuration: dict[str, Any]) -> None:
    """
        Reads remote configuration values into the GUI fields.
        
        :param parent: The main GUI where this function is being called.
        :type parent: ZaberMainWindow
        :param configuration: The configuration from the remote GUI.
        :type configuration: dict[str, Any]
        :return: None
        :rtype: None
    """
    for widgetName, attribute in attributeWidgetLookup.inv.items():
        getattr(parent, widgetName).setValue(configuration[attribute])
    logger.info(f"Read Proportional configuration from controller.")

def validateProportionalConfiguration(configuration: dict[str, Any]) -> bool:
    """
        Validates the configuration from the GUI before sending to the remote.

        :param configuration: Configuration from the GUI that should be checked for errors.
        :type configuration: dict[str, Any]
        :return: True if validated correctly, False otherwise
        :rtype: bool
    """
    positionMin = configuration['positionMin']
    positionMax = configuration['positionMax']
    loadcellMin = configuration['loadcellMin']
    loadcellMax = configuration['loadcellMax']

    passedValidationChecks = True

    if positionMax <= positionMin:
        logger.warning(redBoldText(joinStringsWithSpace(f"Minimum Position is greater than or equal to Maximum Position.", 
                                            f"Please check values in Proportional > Position Limits > Minimum Position Limit and Maximum Position Limit.",
                                f"Current Values are Minimum Angle Limit: {positionMin}, Maximum Angle Limit: {positionMax}")))
        passedValidationChecks = False
        
    if loadcellMax <= loadcellMin:
        logger.warning(redBoldText(joinStringsWithSpace(f"Minimum Loadcell is greater than or equal to Maximum Loadcell.",
                                f"Please check values in Proportional > Load Cell Limits > Minimum Load Cell Limit and Maximum Load Cell Limit.",
                        f"Current Values are Minimum Load Cell Limit: {loadcellMin}, Maximum Load Cell Limit: {loadcellMax}")))
        passedValidationChecks = False
    return passedValidationChecks

def writeProportionalConfigurationChanges(parent: ZaberMainWindow, configurationChanges: dict[str, Any]) -> None:
    """
        Writes the control logic parameter values to the remote.

        :param parent: The main GUI where this function is being called.
        :type parent: ZaberMainWindow
        :param configurationChanges: The dictionary of parameters that should be overridden in the remote.
        :type configurationChanges: dict[str, Any]
        :return: None
        :rtype: None
    """
    parent.sendRemoteCommand('changeControlLogicParameters', {'controlLogicType': ControlLogic.ZaberController, 'parameters': configurationChanges, 'index': 0})

def readProportionalConfigurationFromSaveFile() -> None:
    """
        Not defined. No configuration is read from a save file in this example.
    """
    pass

def adjustProportionalPlotThresholdValues() -> None:
    """
        Not defined. No thresholds are defined in this example.
    """
    pass