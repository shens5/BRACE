from PySide6 import QtWidgets
import logging
import tomllib
import brace.UI.example.GUIController.PrefixNames as PrefixNames

logger = logging.getLogger("logger")

def setConfigurationDictionaries(referenceConfigurationNames: list[str], internalDictionary: dict[str, QtWidgets.QWidget]) -> dict[str, QtWidgets.QWidget]:
    """
        Creates a dictionary of the relevant configuration elements referenced by the name for easy access.
        The names are given as prefixes and the relevant widget has the L and R appended.

        :param referenceConfigurationNames: list of configuration name prefixes
        :type referenceConfigurationNames: list[str]
        :param internalDictionary: Dictionary from the configuration box containing the attribute name and the widgets.
        :type internalDictionary: dict[str, QtWidgets.QWidget]
        :return: A consolidated dictionary of left and right widgets containing relevant parameter fields.
        :rtype: dict[str, QtWidgets.QWidget]
    """
    configurationLookup: dict[str, QtWidgets.QWidget] = {}
    for name in referenceConfigurationNames:
        leftConfigurationWidgetName = PrefixNames.formatConfigurationWidgetLeg(name, isLeft = True)
        rightConfigurationWidgetName = PrefixNames.formatConfigurationWidgetLeg(name, isLeft = False)
        if leftConfigurationWidgetName in internalDictionary:
            configurationLookup[leftConfigurationWidgetName] = internalDictionary[leftConfigurationWidgetName]
        if rightConfigurationWidgetName in internalDictionary:
            configurationLookup[rightConfigurationWidgetName] = internalDictionary[rightConfigurationWidgetName]
    return configurationLookup

def setSingleConfigurationDictionaries(referenceConfigurationNames: list[str], internalDictionary: dict[str, QtWidgets.QWidget]) -> dict[str, QtWidgets.QWidget]:
    """ 
        Gets the configuration for any single fields that are assigned for both left and right 
        (and thus do not fit in the use of setConfigurationDictionaries).

        :param referenceConfigurationNames: list of configuration name prefixes
        :type referenceConfigurationNames: list[str]
        :param internalDictionary: Dictionary from the configuration box containing the attribute name and the widgets.
        :type internalDictionary: dict[str, QtWidgets.QWidget]
        :return: A dictionary consisting of relevant single type parameter fields.
        :rtype: dict[str, QtWidgets.QWidget]
    """
    configurationLookup: dict[str, QtWidgets.QWidget] = {}
    for name in referenceConfigurationNames:
        if name in internalDictionary:
            configurationLookup[name] = internalDictionary[name]
    return configurationLookup

# This initializes limits, only for the spinboxes and double-spinboxes.
def initializeLimits(limitInformation: dict[str, dict[str, int | float]], configurationObjects: dict) -> None:
    """
        Initializes the limits for configuration objects using the information set up in the .ini
        file for the minimum, maximum, and stepSize of the configuration object.

        :param limitInformation: The minimum, maximum, and stepSize limits information for the configuration object.
        :type limitInformation: dict[str, dict[str, int | float]]
        :param configurationObjects: The configuration widgets dictionary that references widgets by name.
        :type configurationObjects: dict[str, QtWidgets.QWidget]

        :return: None
        :rtype: None
    """
    for configurationName, configurationDict in limitInformation.items():
        leftName = PrefixNames.formatConfigurationWidgetLeg(configurationName, isLeft = True)
        rightName = PrefixNames.formatConfigurationWidgetLeg(configurationName, isLeft = False)

        configurationObjectsToLimit = [configurationObjects[leftName], configurationObjects[rightName]]
        minimumLimit = configurationDict.get("minimum", configurationObjects[leftName].minimum())
        maximumLimit = configurationDict.get("maximum", configurationObjects[leftName].maximum())
        stepSize = configurationDict.get("stepSize", configurationObjects[leftName].singleStep())

        for configurationObject in configurationObjectsToLimit:
            configurationObject.setRange(minimumLimit, maximumLimit)
            configurationObject.setSingleStep(stepSize)

def initializeDefaultParameters(defaultParameters: dict[str, float], configurationObjects: dict[str, QtWidgets.QWidget]) -> None:
    """
        Sets the default values for the parameters that are listed in the .ini file. Currently
        only QComboBox, QSpinBox, and QDoubleSpinBox are supported.

        :param defaultParameters: The default values for the parameters in the configuration widget.
        :type defaultParameters: dict[str, float]
        :param configurationObjects: The configuration widgets dictionary that references widgets by name.
        :type configurationObjects: dict[str, QtWidgets.QWidget]

        :return: None
        :rtype: None
    """
    for defaultParameter, defaultValue in defaultParameters.items():
        leftName = PrefixNames.formatConfigurationWidgetLeg(defaultParameter, isLeft = True)
        rightName = PrefixNames.formatConfigurationWidgetLeg(defaultParameter, isLeft = False)
        
        configurationObjectsToDefault = [configurationObjects[leftName], configurationObjects[rightName]]
        for configurationObject in configurationObjectsToDefault:
            if isinstance(configurationObject, QtWidgets.QComboBox):
                configurationObject.setCurrentIndex(int(defaultValue))
            elif isinstance(configurationObject, QtWidgets.QSpinBox):
                configurationObject.setValue(int(defaultValue))
            elif isinstance(configurationObject, QtWidgets.QDoubleSpinBox):
                configurationObject.setValue(defaultValue)

def initializeLegEntries(legInformation: dict[str, dict], legComboBoxLeft: QtWidgets.QComboBox, legComboBoxRight: QtWidgets.QComboBox) -> None:
    """
        Populates the entries in the .ini file with the relevant
        leg entries of the combobox.

        :param legInformation: Dictionary containing the string and other relevant information of the leg serial.
        :type legInformation: dict[str, dict]
        :param legComboBoxLeft: The left combobox leg for the leg to be populated with entries.
        :type legComboBoxLeft: QtWidgets.QComboBox
        :param legComboBoxRight: The right combobox leg for the leg to be populated with entries.
        :type legComboBoxRight: QtWidgets.QComboBox
    
        :return: None
        :rtype: None
    """
    leftLegs = []
    rightLegs = []
    for legName, legParameters in legInformation.items():
        legSide: str = legParameters.get("legSide", "").strip()
        if legSide == "left":
            leftLegs.append(legName)
        elif legSide == "right":
            rightLegs.append(legName)
        else:
            logger.error(f"Error in ExoskeletonControl.ini. Entry: [{legName}]. " +
                            "Configuration parameter 'legSide' must be 'left' or 'right'.")
    legComboBoxLeft.addItems(leftLegs)
    legComboBoxRight.addItems(rightLegs)

def loadInitFile(fileLocation: str) -> dict:
    """
        Load the .ini file, which is intended to be a toml file. It is formatted as a nested dictionary.

        :return: A dictionary containing the information inside the .ini file.
        :rtype: dict[str, Any]
    """
    with open(fileLocation, 'rb') as legConfigurationFile:
        initializationConfiguration = tomllib.load(legConfigurationFile)
    return initializationConfiguration

def getDefaultsDictionary(initFileConfiguration: dict) -> dict | None:
    """
        Gets the subdictionary under "defaults"

        :param initFileConfiguration: The default values for the configuration.
        :type initFileConfiguration: dict[str, float | int]

        :return: Subdictionary underneath the defaults header
        :rtype: dict[str, Any]
    """
    initFileDefaults = initFileConfiguration.get('defaults', None)
    return initFileDefaults

def getSettingsDictionary(initFileConfiguration: dict) -> dict | None:
    """
        Gets the subdictionary under "settings"

        :param initFileConfiguration: The default values for the configuration.
        :type initFileConfiguration: dict[str, float | int]

        :return: Subdictionary underneath the settings header
        :rtype: dict[str, Any]
    """
    initFileSettings = initFileConfiguration.get('settings', None)
    return initFileSettings