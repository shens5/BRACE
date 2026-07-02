import brace.UI.example.GUIController.WalkUIConfiguration as WalkUIConfiguration
import brace.UI.example.GUIController.ProportionalUIConfiguration as ProportionalUIConfiguration
import brace.UI.example.GUIController.StandingUIConfiguration as StandingUIConfiguration

# Names of configuration prefixes that can be saved and loaded out
configurationWidgetNamePrefixes = [*WalkUIConfiguration.configurationWidgetPrefixes,
                                    *ProportionalUIConfiguration.configurationWidgetPrefixes,
                                    *StandingUIConfiguration.configurationWidgetPrefixes]

configurationSingleWidgetNamePrefixes = []

# Names of configuration labels that may have toggled visibility, these are the ones assigned to the "L" and "R" legs.
configurationNameLabelPrefixes = [*WalkUIConfiguration.configurationNameLabelPrefixes,
                                    *ProportionalUIConfiguration.configurationNameLabelPrefixes,
                                    *StandingUIConfiguration.configurationNameLabelPrefixes]

def getLegSideShort(isLeft: bool) -> str:
    """
        Returns a shorthand for whether or not the leg is left or right.

        :params isLeft: Whether or not the leg is left or right:
        :type isLeft: bool

        :return: Short string of the leg representing left and right.
        :rtype: str    
    """
    return "L" if isLeft else "R"

def getLegSideLong(isLeft: bool) -> str:
    """
        Returns a longhand for whether or not the leg is left or right.

        :params isLeft: Whether or not the leg is left or right:
        :type isLeft: bool

        :return: Longer string of the leg representing left and right.
        :rtype: str    
    """
    return "Left" if isLeft else "Right"

def formatConfigurationWidgetLeg(configurationObjectName: str, isLeft: bool) -> str:
    """
        Formats the configuration widgets with short leg suffix. If the name is contained in configurationSingleWidgetNamePrefixes,
        then it is formatted as regular.

        :params configurationObjectName: the name of the widget to be formatted
        :type configurationObjectName: str
        :params isLeft: Whether or not the leg is left or right.
        :type isLeft: bool

        :return: Configuration widget leg formatted with the short leg suffix.
        :rtype: str
    """
    if configurationObjectName in configurationSingleWidgetNamePrefixes:
        return configurationObjectName
    else:
        return f"{configurationObjectName}{getLegSideShort(isLeft = isLeft)}"
    
def getConfigurationWidgetSideFromName(configurationWidgetName: str) -> bool | None:
    """
        Determines whether or not the widget is from the left or right side. Returns True if left, false if right, and None if neither.

        :params configurationWidgetName: Name of the configuration widget.
        :type configurationWidgetName: str

        :return: Boolean or None defining the side that the configuration widget belongs to.
        :rtype: bool | None
    """
    if configurationWidgetName.endswith("L"):
        return True # is left
    elif configurationWidgetName.endswith("R"):
        return False # is right
    else:
        return None # is neither

def getLeftRightIndex(isLeft: bool) -> int:
    """
        Converts left/right to the recognized index on the remote side. (0 is defined as left, 1 is considered right).

        :params isLeft: Whether or not the leg is left or right.
        :type isLeft: bool

        :return: The recognized index for the remote side.
        :rtype: int
    """
    return int(not isLeft)