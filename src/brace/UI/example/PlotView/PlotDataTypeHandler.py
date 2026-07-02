from __future__ import annotations
from abc import abstractmethod
from typing import Any, override
import math
from pyqtgraph.widgets.MatplotlibWidget import MatplotlibWidget

import brace.UI.example.PlotConfiguration.ConfiguredWalkPlots as ConfiguredWalkPlots
import brace.UI.example.PlotConfiguration.ConfiguredProportionalPlots as ConfiguredProportionalPlots
import brace.UI.example.PlotConfiguration.ConfiguredStandingPlots as ConfiguredStandingPlots
import brace.UI.example.PlotConfiguration.ConfiguredTriggerPlots as ConfiguredTriggerPlots
import brace.UI.PlotConfiguration.ConfigurePlotHelpers as ConfigurePlotHelpers

from typing import NamedTuple
from brace.example.exoskeleton.ControlLogic.FSM import FSM5
from brace.example.exoskeleton.ControlLogic.ProportionalControlLogic import Proportional
from brace.example.exoskeleton.ControlLogic.Standing import Standing
from brace.Server.GPIOSynch.PushButton import Trigger

class IDataTypeHandler():
    """
        Interface that handles reading datatypes from a data stream file. One data type handler must be written
        for each new type that is being read. Must contain the DataType (NamedTuple), the PlotHandler (MplBasePlot).
        The PyQtPlotHandler is there for completion.
    """
    DataType: NamedTuple = None
    PlotHandler: ConfigurePlotHelpers.MplBasePlot = None
    PyQtPlotHandler: ConfigurePlotHelpers.PyQTBasePlot = None

    @abstractmethod
    def getConfigurableValues(configDictionary: dict[str, Any]) -> dict[str, Any]:
        """
            Return a subset of the configured values that are in the saved stream file.
            These values are to be used in the plots (typically for thresholds).

            :params configDictionary: A dictionary containing the configuration values for the datatype.
            :type configDictionary: dict[str, Any]
            :return: A subset dictionary containing the configuration values to be used in the plots.
            :rtype: dict[str, Any]
        """
        pass

    @abstractmethod
    def configurePlots(plotWidget: MatplotlibWidget, configurationToDisplay: dict[str, Any]) -> ConfigurePlotHelpers.MplBasePlot:
        """
            This creates the plot using the MplBasePlot to be used in opening files.

            :params plotWidget: The widget to be used in graphing this particular plot.
            :type plotWidget: MatplotlibWidget:
            :params configurationToDisplay: The configuration that should be passed in 
            for configured parameters in the plots (such as thresholds).
            :type configurationToDisplay: dict[str, Any]

            :return: A configured set of plots to be used in the matplotlib widget.
            :rtype: ConfigurePlotHelpers.MplBasePlot
        """
        pass

    @abstractmethod
    def updateFinalPlot(configurePlotObject: ConfigurePlotHelpers.MplBasePlot) -> None:
        """
            Runs as a hook to override any autoscaled graphing in the final plots.

            :params configurePlotObject: The plots that are drawn.
            :type configurePlotObject: ConfigurePlotHelpers.MplBasePlot

            :return: None
            :rtype: None 
        """
        pass

def configDictionaryisNan(configDictionary: dict | float | None) -> bool:
    """
        Check to see if the configuration dictionary is NaN (and thus there is no configuration dictionary). Refers
        to an inactive leg.
        
        :param configDictionary: Dictionary (or NaN float) to check for configuration.
        :type configDictionary: dict | float

        :return: None
        :rtype: None
    """
    return isinstance(configDictionary, float) and math.isnan(configDictionary)

class FSM5Handler(IDataTypeHandler):
    """
        Data handler for the Walking Controller (aka FSM5).
    """
    DataType = FSM5
    PlotHandler = ConfiguredWalkPlots.WalkPlotsMpl
    PyQtPlotHandler = ConfiguredWalkPlots.WalkPlotsPyQt

    @override
    def getConfigurableValues(configDictionary: dict[str, Any]) -> dict[str, Any]:
        # There are a total of 5 configurations that should be read out (Left and right independently of each other).
        # These are the FSR Swing and initial contact values, and velocities for each transition within stance and swing.
        configurationToDisplay = {}
        if configDictionary:
            if (fsmConfiguration := configDictionary[FSM5.__name__]['L']) is not None and not configDictionaryisNan(fsmConfiguration):
                configurationToDisplay['forceSensorThresholdInitialContactL'] = fsmConfiguration['forceSensorThresholdInitialContact']
                configurationToDisplay['forceSensorThresholdSwingL'] = fsmConfiguration['forceSensorThresholdSwing']
                configurationToDisplay['velocityEarlyToMidStanceThresholdL'] = fsmConfiguration['velocityEarlyToMidStanceThreshold']
                configurationToDisplay['velocityMidToLateStanceThresholdL'] = fsmConfiguration['velocityMidToLateStanceThreshold']
                configurationToDisplay['velocityEarlyToLateSwingThresholdL'] = fsmConfiguration['velocityEarlyToLateSwingThreshold']

            if (fsmConfiguration := configDictionary[FSM5.__name__]['R']) is not None and not configDictionaryisNan(fsmConfiguration):
                configurationToDisplay['forceSensorThresholdInitialContactR'] = fsmConfiguration['forceSensorThresholdInitialContact']
                configurationToDisplay['forceSensorThresholdSwingR'] = fsmConfiguration['forceSensorThresholdSwing']
                configurationToDisplay['velocityEarlyToMidStanceThresholdR'] = fsmConfiguration['velocityEarlyToMidStanceThreshold']
                configurationToDisplay['velocityMidToLateStanceThresholdR'] = fsmConfiguration['velocityMidToLateStanceThreshold']
                configurationToDisplay['velocityEarlyToLateSwingThresholdR'] = fsmConfiguration['velocityEarlyToLateSwingThreshold']
        return configurationToDisplay

    @override
    def configurePlots(plotWidget: MatplotlibWidget, configurationToDisplay: dict[str, Any]) -> ConfiguredWalkPlots.WalkPlotsMpl:
        return ConfiguredWalkPlots.WalkPlotsMpl(plotWidget, **configurationToDisplay)

    @override
    def updateFinalPlot(configurePlotObject: ConfiguredWalkPlots.WalkPlotsMpl) -> None:
        configurePlotObject.updateFinalPlotMatplotlib()

class ProportionalHandler(IDataTypeHandler):
    """
        Data handler for the Proportional Controller.
    """
    DataType = Proportional
    PlotHandler = ConfiguredProportionalPlots.ProportionalPlotsMpl
    PyQtPlotHandler = ConfiguredProportionalPlots.ProportionalPlotsPyQt

    @override
    def getConfigurableValues(configDictionary: dict[str, Any]) -> dict[str, Any]:
        return {}

    @override
    def configurePlots(plotWidget: MatplotlibWidget, configurationToDisplay: dict[str, Any]) -> ConfiguredProportionalPlots.ProportionalPlotsMpl:
        return ConfiguredProportionalPlots.ProportionalPlotsMpl(plotWidget, **configurationToDisplay)
    
class StandingHandler(IDataTypeHandler):
    """
        Data handler for the Standing Controller.
    """
    DataType = Standing
    PlotHandler = ConfiguredStandingPlots.StandingPlotsMpl
    PyQtPlotHandler = ConfiguredStandingPlots.StandingPlotsPyQt

    @override
    def getConfigurableValues(configDictionary: dict[str, Any]) -> dict[str, Any]:
        configurationToDisplay = {}
        return configurationToDisplay

    @override
    def configurePlots(plotWidget: MatplotlibWidget, configurationToDisplay: dict[str, Any]) -> ConfiguredStandingPlots.StandingPlotsMpl:
        return ConfiguredStandingPlots.StandingPlotsMpl(plotWidget, **configurationToDisplay)

class TriggerHandler(IDataTypeHandler):
    """
        Data handler for the Trigger (Not a controller, but handled the same way).
    """
    DataType = Trigger
    PlotHandler = ConfiguredTriggerPlots.TriggerPlotsMpl
    PyQtPlotHandler = ConfiguredStandingPlots.StandingPlotsPyQt

    @override
    def getConfigurableValues(configDictionary: dict[str, Any]) -> dict[str, Any]:
        configurationToDisplay = {}
        return configurationToDisplay

    @override
    def configurePlots(plotWidget: MatplotlibWidget, configurationToDisplay: dict[str, Any]) -> ConfiguredTriggerPlots.TriggerPlotsMpl:
        return ConfiguredTriggerPlots.TriggerPlotsMpl(plotWidget, **configurationToDisplay)

    @override
    def updateFinalPlot(configurePlotObject: ConfiguredTriggerPlots.TriggerPlotsMpl) -> None:
        configurePlotObject.updateFinalPlotMatplotlib()

def getDataTypeHandler(dataType: str) -> IDataTypeHandler | None:
    """
        Static list of handlers that should be used for each data type. Returns the appropriate
        one based on the dataType name given.

        :param dataType: The data type that is found in the data file.
        :type dataType: str

        :return: The handler for the data type that we should use.
        :rtype: IDataTypeHandler
    """
    handlers = [FSM5Handler, ProportionalHandler, StandingHandler, TriggerHandler]
    types = {handler.DataType.__name__: handler for handler in handlers}
    return types.get(dataType, None)