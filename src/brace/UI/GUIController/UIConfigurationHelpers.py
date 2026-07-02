from __future__ import annotations
import json
from pathlib import Path
from typing import TYPE_CHECKING, Any
from PySide6.QtWidgets import QAbstractSpinBox, QComboBox, QFileDialog, QWidget
from PySide6.QtCore import Slot
from brace.UI.example.GUIController import PrefixNames
if TYPE_CHECKING:
    from brace.UI.example.MainWindow import MainWindow
    from brace.UI.example.Simulator import Simulator

import logging
logger = logging.getLogger("logger")

def getConfigurationChanges(configurationObjects: dict[str, QWidget], configurationWidgetLookup: dict[str, str]) -> tuple[dict[str, str | int | float]]:
    """
        Gets the configuration values for both left and right configuration fields and places
        them into two separate dictionaries.

        :param configurationObjects: The configuration widget objects referenceable by name.
        :type configurationObjects: dict[str, QWidget]
        :param configurationWidgetLookup: A lookup between the name of the attribute in the remote control logic object
        and the name of the field as the configuration widget.
        :type configurationWidgetLookup: dict[str, str]

        :return: Left and right configuration referencing the configuration widget name instead of the control logic object name.
        :rtype: tuple[dict[str, str | int | float]]
    """
    leftConfigurationChanges = {}
    rightConfigurationChanges = {}
    for configurationName, widgetPrefix in configurationWidgetLookup.items():
        leftObject, rightObject = getLegElementsByPrefix(configurationObjects, widgetPrefix)

        if rightObject is None: # For elements that don't have a "right" leg. One element for both legs.
            rightConfigurationChanges[configurationName] = leftConfigurationChanges[configurationName] = leftObject.currentText()
        elif isinstance(leftObject, QComboBox) and isinstance(rightObject, QComboBox):
            leftConfigurationChanges[configurationName] = leftObject.currentText()
            rightConfigurationChanges[configurationName] = rightObject.currentText()
        else: # These are either spinboxes or double spinboxes.        
            leftConfigurationChanges[configurationName] = leftObject.value()
            rightConfigurationChanges[configurationName] = rightObject.value()
    
    return leftConfigurationChanges, rightConfigurationChanges

def getLegElementsByPrefix(configurationObjects: dict[str, QWidget], widgetPrefix: str) -> tuple[QWidget, QWidget]:
    """
        Gets the tuple of left and right configuration widget objects using the widget prefix.

        :param configurationObjects: Dictionary of configuration widget objects referenced by name.
        :type configurationObjects: dict[str, QWidget]
        :param widgetPrefix: The prefix of the widget, this function determines the left and right names.
        :type widgetPrefix: str
        
        :return: The left and right leg QWidget elements. 
        :rtype: tuple[QWidget, QWidget]
    """
    leftLegElementName = PrefixNames.formatConfigurationWidgetLeg(widgetPrefix, True)
    rightLegElementName = PrefixNames.formatConfigurationWidgetLeg(widgetPrefix, False)
    # added to handle the Lead Leg Combo boxes that only have one setting for both legs.
    if widgetPrefix in PrefixNames.configurationSingleWidgetNamePrefixes: 
        return (configurationObjects[widgetPrefix], None)
    return (configurationObjects[leftLegElementName], configurationObjects[rightLegElementName])

def hideItem(configurationWidgetName: str, configurationWidgetObject: QWidget, 
             hideLeftLegConfiguration: bool, hideRightLegConfiguration: bool) -> None:
    """
        Hides or shows the leg widget items. This is done when the leg is not active.
        If at least one leg is active, then leg widgets that belong to both will be shown.

        :param configurationWidgetName: Name of the configuration widget.
        :type configurationWidgetName: str
        :param configurationWidgetObject: The configuration widget to hide or show.
        :type configurationWidgetObject: QWidget
        :param hideLeftLegConfiguration: Whether or not the left leg configuration should be hidden or shown.
        :type hideLeftLegConfiguration: bool
        :param hideRightLegConfiguration: Whether or not the right leg configuration should be hidden or shown.
        :type hideRightLegConfiguration: bool

        :return: None
        :rtype: None
    """
    hideOrShow = configurationWidgetObject.show
    configurationLegWidgetSide = PrefixNames.getConfigurationWidgetSideFromName(configurationWidgetName)
    if configurationLegWidgetSide is None: # Both
        hideOrShow = configurationWidgetObject.hide if hideLeftLegConfiguration and hideRightLegConfiguration else hideOrShow
    elif configurationLegWidgetSide: # Left
        hideOrShow = configurationWidgetObject.hide if hideLeftLegConfiguration else hideOrShow
    elif not configurationLegWidgetSide: # Right
        hideOrShow = configurationWidgetObject.hide if hideRightLegConfiguration else hideOrShow
    hideOrShow()

def getLegElementsByPrefix(configurationObjectsNew: dict[str, QWidget], widgetPrefix: str) -> tuple[QWidget, QWidget]:
    """
        Gets tuple of leg elements with a given prefix.

        :param configurationObjectsNew: Dictionary of QWidgets referenced by name.
        :type configurationObjectsNew: dict[str, QWidget]
        :param widgetPrefix: The prefix for a given QWidget that should be referenced.
        :type widgetPrefix: str

        :return: A tuple of QWidget objects retrieved given the widgetPrefix. Belonging to both belongs to the first element
        in the tuple.
        :rtype: tuple[QWidget, QWidget]
    """
    leftLegElementName = PrefixNames.formatConfigurationWidgetLeg(widgetPrefix, True)
    rightLegElementName = PrefixNames.formatConfigurationWidgetLeg(widgetPrefix, False)
    # added to handle the Lead Leg Combo boxes that only have one setting for both legs.
    if widgetPrefix in PrefixNames.configurationSingleWidgetNamePrefixes: 
        return (configurationObjectsNew[widgetPrefix], None)
    return (configurationObjectsNew[leftLegElementName], configurationObjectsNew[rightLegElementName])

@Slot()
def saveConfiguration(parent: MainWindow | Simulator, configurationObjects: dict[str, QWidget]) -> None:
    """
        Saves the configuration as a JSON file. This can be done from either the main GUI or the Simulator.
        The JSON file handles the configuration using the widget object names. The JSON is formatted with 4 spaces.

        :param parent: The calling GUI running this function.
        :type parent: MainWindow | Simulator
        :param configurationObjects: The configuration widgets referenced by widget name.
        :type configurationObjects: dict[str, QWidget]

        :return None
        :rtype None
    """
    configurationData = getConfigurationParametersFromGUI(parent, configurationObjects)
    options = QFileDialog.Option()
    fileName, _ = QFileDialog.getSaveFileName(parent, "Save Configuration File", "", "JSON Files (*.json)", options = options)
    
    if fileName:
        if Path(fileName).suffix != '.json':
            fileName = Path(fileName).with_suffix('.json')

        with open(fileName, 'w+') as savedConfigurationFile:
            json.dump(configurationData, savedConfigurationFile, indent = 4)
            logger.info(f"Saved Configuration File: {fileName}.")

def getConfigurationParametersFromGUI(parent: MainWindow | Simulator, configurationObjects: dict[str, QWidget]) -> dict[str, Any]:
    """
        Helper function that gets the configuration values from the GUI. Configuration
        is obtained using the widget name. Only active legs are exported. Thus one left and right leg configurations
        can be merged by opening separately.

        :param parent: The calling GUI running this function.
        :type parent: MainWindow | Simulator
        :param configurationObjects: The configuration widgets referenced by widget name.
        :type configurationObjects: dict[str, QWidget]

        :return: A dictionary containing all of the widget names and values.
        :rtype: dict[str, Any]
    """
    def getValueFromElement(field: QWidget) -> int | float:
        if isinstance(field, QAbstractSpinBox):
            return field.value()
        elif isinstance(field, QComboBox):
            return field.currentIndex()
    
    configurationParameters = {}
    for name in [*PrefixNames.configurationWidgetNamePrefixes, *PrefixNames.configurationSingleWidgetNamePrefixes]:
        leftElementField, rightElementField = getLegElementsByPrefix(configurationObjects, name)

        if parent.isLeftLegActive() and leftElementField is not None:
            configurationParameters[leftElementField.objectName()] = getValueFromElement(leftElementField)
        if parent.isRightLegActive() and rightElementField is not None:
            configurationParameters[rightElementField.objectName()] = getValueFromElement(rightElementField)
    return configurationParameters