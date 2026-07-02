from __future__ import annotations
from brace.example.exoskeleton.ControlLogic.FSM import States
from brace.example.exoskeleton.ControlLogicLookup import ControlLogicEnum
from brace.UI.ConfigurationGrid import ConfigurationGrid
import brace.UI.example.PlotConfiguration.ConfiguredWalkPlots as ConfiguredWalkPlots 
import brace.UI.example.GUIController.PrefixNames as PrefixNames
import brace.UI.GUIController.UIConfigurationHelpers as UIConfigurationHelpers
from PySide6.QtWidgets import QWidget
from brace.UI.LoggingHelpers import redBoldText, joinStringsWithSpace
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from brace.UI.example.MainWindow import MainWindow
import logging
logger = logging.getLogger("logger")

configurationWidgetLookup = {
        'forceSensorThresholdInitialContact': 'walkFSM5IcThresholdSpinBox',
        'forceSensorThresholdSwing': 'walkFSM5ToThresholdSpinBox',
        'deadZoneTime': 'walkFSM5DeadZoneTimeDoubleSpinBox',
        'velocityEarlyToMidStanceThreshold': 'walkFSM5EarlyToMidStanceThresholdSpinBox',
        'velocityMidToLateStanceThreshold': 'walkFSM5MidToLateStanceThresholdSpinBox',
        'velocityEarlyToLateSwingThreshold': 'walkFSM5EarlyToLateSwingThresholdSpinBox',
        'timeoutTime': 'walkFSM5TimeoutToWaitingDoubleSpinBox',
        'extAngleLimit': 'walkFSM5ExtLimitSpinBox',
        'flexAngleLimit': 'walkFSM5FlexLimitSpinBox',
        'stanceRampRate': 'walkFSM5StanceRampRateSpinBox',
        'swingRampRate': 'walkFSM5SwingRampRateSpinBox'
    }

configurationWidgetPrefixes = list(configurationWidgetLookup.values()) + ['walkFSM5EarlyStanceTorqueDoubleSpinBox',
                               'walkFSM5MidStanceTorqueDoubleSpinBox',
                               'walkFSM5LateStanceTorqueDoubleSpinBox',
                               'walkFSM5EarlySwingTorqueDoubleSpinBox',
                               'walkFSM5LateSwingTorqueDoubleSpinBox']

configurationNameLabelPrefixes = ['walkFSM5PhasesLegLabel',
                                  'walkFSM5SubPhasesLegLabel',
                                  'walkFSM5AngleLimitsLegLabel',
                                  'walkFSM5RampRatesLegLabel',
                                  'walkFSM5TorqueLegLabel',
                                  'walkFSM5TimeoutsLegLabel']

changeableThresholds = ConfiguredWalkPlots.WalkPlotsPyQt.velocityKeywords + ConfiguredWalkPlots.WalkPlotsPyQt.thresholdKeywords

def getWalkConfigurationChanges(configurationObjects: dict[str, QWidget], configurationGrid: ConfigurationGrid) -> tuple[dict[str, Any], dict[str, Any]]:
    """
        Gets the configuration for the walk controller from the GUI box divided by left and right.

        :params configurationObjects: dictionary containing the QWidgets referenced by name.
        :type configurationObjects: dict[str, QWidget]
        :params configurationGrid: Configuration Grid object that contains all of the fields.
        :type configurationGrid: ConfigurationGrid

        :return: Tuple of configuration widgets that were assigned for the legs. 
        :rtype: tuple[dict[str, Any], dict[str, Any]]
    """
    leftConfigurationChanges, rightConfigurationChanges = UIConfigurationHelpers.getConfigurationChanges(configurationObjects, configurationWidgetLookup)

    leftConfigurationChanges['stateTorques'] = { States.WAITING: 0,
                            States.EARLY_STANCE: configurationGrid.walkFSM5EarlyStanceTorqueDoubleSpinBoxL.value(),
                            States.MID_STANCE: configurationGrid.walkFSM5MidStanceTorqueDoubleSpinBoxL.value(),
                            States.LATE_STANCE: configurationGrid.walkFSM5LateStanceTorqueDoubleSpinBoxL.value(),
                            States.EARLY_SWING: configurationGrid.walkFSM5EarlySwingTorqueDoubleSpinBoxL.value(),
                            States.LATE_SWING: configurationGrid.walkFSM5LateSwingTorqueDoubleSpinBoxL.value() }
    
    rightConfigurationChanges['stateTorques'] = { States.WAITING: 0,
                            States.EARLY_STANCE: configurationGrid.walkFSM5EarlyStanceTorqueDoubleSpinBoxR.value(),
                            States.MID_STANCE: configurationGrid.walkFSM5MidStanceTorqueDoubleSpinBoxR.value(),
                            States.LATE_STANCE: configurationGrid.walkFSM5LateStanceTorqueDoubleSpinBoxR.value(),
                            States.EARLY_SWING: configurationGrid.walkFSM5EarlySwingTorqueDoubleSpinBoxR.value(),
                            States.LATE_SWING: configurationGrid.walkFSM5LateSwingTorqueDoubleSpinBoxR.value() }
    return leftConfigurationChanges, rightConfigurationChanges

                               
def writeWalkConfigurationChanges(parent: MainWindow, leftConfigurationChanges: dict[str, Any], rightConfigurationChanges: dict[str, Any]) -> None:
    """
        Writes the configuration changes from the client to the remote.

        :params parent: The MainWindow object that is calling this function.
        :type parent: MainWindow
        :params leftConfigurationChanges: The configuration changes that should be written, belonging to the left leg.
        :type leftConfigurationChanges: dict[str, Any]
        :params rightConfigurationChanges: The configuration changes that should be written, belonging to the right leg.
        :type rightConfigurationChanges: dict[str, Any]

        :return: None
        :rtype: None
    """
    if parent.isLeftLegActive():
        parent.sendRemoteCommand('changeControlLogicParameters', {'controlLogicType': ControlLogicEnum.FSM5, 'parameters': leftConfigurationChanges, 'index': PrefixNames.getLeftRightIndex(True)})

    if parent.isRightLegActive():
        parent.sendRemoteCommand('changeControlLogicParameters', {'controlLogicType': ControlLogicEnum.FSM5, 'parameters': rightConfigurationChanges, 'index': PrefixNames.getLeftRightIndex(False)})
        
def _setWalkPlotThresholdValues(parent: MainWindow, velocityEarlyToMidStanceThreshold: float, velocityMidToLateStanceThreshold: float, velocityEarlyToLateSwingThreshold: float,
                           forceSensorThresholdInitialContact: float, forceSensorThresholdSwing: float, isLeft: bool) -> None:
    walkGraphContext = parent.graphContexts[parent.walkGraphContextIndex]
    ConfiguredWalkPlots.WalkPlotsPyQt.setThresholdValues(walkGraphContext.axes, velocityEarlyToMidStanceThreshold, velocityMidToLateStanceThreshold, velocityEarlyToLateSwingThreshold, 
                                                         forceSensorThresholdInitialContact, forceSensorThresholdSwing, isLeft)
    
def adjustWalkPlotThresholdValues(parent: MainWindow, leftConfigurationChanges: dict[str, Any], rightConfigurationChanges: dict[str, Any]) -> None:
    """
        Changes the threshold values (public facing) functions. Only if the leg is active.

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
        _setWalkPlotThresholdValues(parent, **{thresholdName: leftConfigurationChanges[thresholdName] for thresholdName in changeableThresholds}, isLeft = True)

    if parent.isRightLegActive():
        _setWalkPlotThresholdValues(parent, **{thresholdName: rightConfigurationChanges[thresholdName] for thresholdName in changeableThresholds}, isLeft = False)
    
def _translateWalkConfiguration(configuration: dict[str, float | dict], stringEnum: bool = False) -> None:

    replacementTable = {objectPrefix: configuration[keyword] for keyword, objectPrefix in configurationWidgetLookup.items()}
    states = [States(i).name if stringEnum else States(i) for i in range(1, len(States))] 

    replacementTable.update({'walkFSM5EarlyStanceTorqueDoubleSpinBox': configuration['stateTorques'][states[0]],
                                'walkFSM5MidStanceTorqueDoubleSpinBox': configuration['stateTorques'][states[1]],
                                'walkFSM5LateStanceTorqueDoubleSpinBox': configuration['stateTorques'][states[2]],
                                'walkFSM5EarlySwingTorqueDoubleSpinBox': configuration['stateTorques'][states[3]],
                                'walkFSM5LateSwingTorqueDoubleSpinBox': configuration['stateTorques'][states[4]]})
    return replacementTable

def readWalkConfigurationFromController(parent: MainWindow, configuration: dict[str, Any], isLeft: bool) -> None:
    """
        Read the standing configuration from the controller remote into the GUI fields.
    
        :params parent: The MainWindow object that is calling this function.
        :type parent: MainWindow
        :params configuration: The configuration from the remote that the fields should be changed into.
        :type configuration: dict[str, Any]
        :params isLeft: Whether or not the fields belong to the left or right legs.
        :type isLeft: bool

        :return: None
        :rtype: None
    """
    replacementTable = _translateWalkConfiguration(configuration, False)
    for configurationObjectName, configurationObjectValue in replacementTable.items():
        parent.configurationObjects[PrefixNames.formatConfigurationWidgetLeg(configurationObjectName, isLeft)].setValue(configurationObjectValue)

    _setWalkPlotThresholdValues(parent, **{thresholdName: configuration[thresholdName] for thresholdName in changeableThresholds}, isLeft = isLeft)
    logger.info(f"Read Walk configuration from controller on {PrefixNames.getLegSideLong(isLeft)} leg.")

def readWalkConfigurationFromSaveFile(configurationObjects: dict[str, QWidget], configuration: dict[str, float | dict], isLeft: bool) -> None:
    """
        Read the configuration for the walking controller from the saved configuration file into the Walking Configuration GUI fields.

        :params configurationObjects: A dictionary containing the widgets, referenced by keyword name.
        :type configurationObjects: dict[str, QWidget]
        :params configuration: The values from the configuration file that should be changed into.
        :type configuration: dict[str, Any]
        :params isLeft: Whether or not the fields belong to the left or right legs.
        :type isLeft: bool

        :return: None
        :rtype: None
    """
    replacementTable = _translateWalkConfiguration(configuration, True)
    for configurationObjectName, configurationObjectValue in replacementTable.items():
        configurationObjects[PrefixNames.formatConfigurationWidgetLeg(configurationObjectName, isLeft)].setValue(configurationObjectValue)

def validateWalkConfiguration(configurationBox: ConfigurationGrid, legActive: bool, isLeft: bool, configuration: dict[str, float]) -> bool:
    """
        Validates the configuration for the walking controller GUI fields. Returns True if valid and false otherwise.

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
    
    icThreshold = configuration['forceSensorThresholdInitialContact']
    toThreshold = configuration['forceSensorThresholdSwing']
    extLimit = configuration['extAngleLimit']
    flexLimit = configuration['flexAngleLimit']

    legSide = PrefixNames.getLegSideLong(isLeft = isLeft)
    passedValidationChecks = True

    if legActive:
        if icThreshold <= toThreshold:
            logger.warning(redBoldText(joinStringsWithSpace(f"{legSide} IC is less than or equal to TO.", 
                                                f"Please check values in Walk-FSM5 > Phases > IC Threshold and TO Threshold ({legSide}).",
                                    f"Current Values are IC Threshold: {icThreshold}, TO Threshold: {toThreshold}")))
            passedValidationChecks = False
        
        if extLimit >= flexLimit:
            logger.warning(redBoldText(joinStringsWithSpace(f"{legSide} Extension Limit is greater than or equal to Flexion Limit.",
                                    f"Please check values in Walk-FSM5 > Angle Limits > Extension limit and Flexion Limit ({legSide}). ",
                            f"Current Values are Extension Limit: {extLimit}, Flexion Limit: {flexLimit}")))
            passedValidationChecks = False
    return passedValidationChecks