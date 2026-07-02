from __future__ import annotations
from enum import IntEnum
import numpy as np
from PySide6.QtWidgets import QHBoxLayout
from pyqtgraph import PlotDataItem, PlotItem
from typing import Any, Callable
from PySide6.QtWidgets import QWidget
from brace.UI.ConfigurationGrid import ConfigurationGrid
from brace.UI.PlotConfiguration.ConfigurePlotHelpers import HideableElementsGraphicsLayoutWidget

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from brace.UI.example.Simulator import Simulator
    from brace.UI.example.MainWindow import MainWindow

class GraphContext():
    """
        A GraphContext wraps up a set of related widgets, datatypes, and callable functions that should be
        used together especially with the context of the GUI.

        :param fig: The HideableElementsGraphicsLayoutWidget or GraphicsLayoutWidget that contains the plots.
        :type fig: HideableElementsGraphicsLayoutWidget
        :param axes: The array of PlotItems that the fig contains.
        :type axes: numpy.ndarray[PlotItem]
        :param axisLines: The dictionary that organizes the graph lines hierarchically by type then by attribute.
        :type axisLines: dict[type, dict[str, Line2D]]
        :param simulatorAxisLines: The dictionary that organizes simulator graph lines hierarchically by type then by attribute.
        :type simulatorAxisLines: dict[type, dict[str, PlotDataItem]]
        :param toggleHBoxLayout: The small horizontal box layout that contains programmatically defined checkboxes for hiding/showing
        checkboxes for the plots.
        :type toggleHBoxLayout: QHBoxLayout
        :param dataType: The data type that overall belongs to this particular set of plots.
        :type dataType: type
        :param controlLogicType: The enum of the respective control logic with this particular dataset.
        :type controlLogicType: IntEnum
        :param getConfigurationChangesFunc: A Callable function that gets the current configuration from the GUI
        :type getConfigurationChangesFunc: Callable[[dict[str, QWidget], ConfigurationGrid], tuple[dict[str, Any], dict[str, Any]]]
        :param validateConfigurationFunc: A Callable function that validates the configuration input in the GUI.
        :type validateConfigurationFunc: Callable[[ConfigurationGrid, bool, bool, dict[str, float]], bool]
        :param writeConfigurationChangesFunc: A Callable function that writes the configuration to the remote and may update threshold lines.
        :type writeConfigurationChangesFunc: Callable[[dict[str, Any], dict[str, Any]], None]
        :param resetGraphXLimitsFunc: A Callable function that resets the graphs back to some initial state before streaming starts again.
        :type resetGraphXLimitsFunc: Callable[[np.ndarray[PlotItem], int], None]
        :param readConfigurationFromControllerFunc: A Callable function that reads the configuration from the remote to the GUI.
        :type readConfigurationFromControllerFunc: Callable[[dict[str, Any], bool], None]
        :param readConfigurationFromSaveFileFunc: A Callable function that reads the configuration from JSON configuration file to the GUI.
        :type readConfigurationFromSaveFileFunc: Callable[[dict[str, QWidget], dict[str, Any], bool], None]
        :param adjustPlotThresholdValuesFunc: A Callable function that adjusts any threshold lines in the plots particularly when parameters are updated.
        :type adjustPlotThresholdValuesFunc: Callable[[MainWindow | Simulator, dict[str, Any], dict[str, Any]], None]
    """

    def __init__(self, fig: HideableElementsGraphicsLayoutWidget, 
                 axes: np.ndarray[PlotItem], 
                 axisLines: dict[type, dict[str, PlotDataItem]],
                 simulatorAxisLines: dict[type, dict[str, PlotDataItem]],
                 toggleHBoxLayout: QHBoxLayout,
                 dataType: type,
                 controlLogicType: IntEnum,
                 getConfigurationChangesFunc: Callable[[dict[str, QWidget], ConfigurationGrid], tuple[dict[str, Any], dict[str, Any]]], # Configuration Grid is for arbitrary values.
                 validateConfigurationFunc: Callable[[ConfigurationGrid, bool, bool, dict[str, float]], bool],
                 writeConfigurationChangesFunc: Callable[[dict[str, Any], dict[str, Any]], None],
                 resetGraphXLimitsFunc: Callable[[np.ndarray[PlotItem], int], None],
                 readConfigurationFromControllerFunc: Callable[[dict[str, Any], bool], None],
                 readConfigurationFromSaveFileFunc: Callable[[dict[str, QWidget], dict[str, Any], bool], None],
                 adjustPlotThresholdValuesFunc: Callable[[MainWindow | Simulator, dict[str, Any], dict[str, Any]], None]):
        self.fig = fig
        self.axes = axes
        self.axisLines = axisLines
        self.simulatorAxisLines = simulatorAxisLines
        self.toggleHBoxLayout = toggleHBoxLayout
        self.dataType = dataType
        self.controlLogicType = controlLogicType
        self.getConfigurationChangesFunc = getConfigurationChangesFunc
        self.validateConfigurationFunc = validateConfigurationFunc
        self.writeConfigurationChangesFunc = writeConfigurationChangesFunc
        self.resetGraphLimitsFunc = resetGraphXLimitsFunc
        self.readConfigurationFromControllerFunc = readConfigurationFromControllerFunc
        self.readConfigurationFromSaveFileFunc = readConfigurationFromSaveFileFunc
        self.adjustPlotThresholdValuesFunc = adjustPlotThresholdValuesFunc