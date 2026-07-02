import itertools

from matplotlib.axes import Axes
from matplotlib.lines import Line2D
import numpy as np
from PySide6.QtWidgets import QHBoxLayout
from pyqtgraph import PlotItem, PlotDataItem
from pyqtgraph.widgets.MatplotlibWidget import MatplotlibWidget

from brace.UI.PlotConfiguration.ConfigurePlotHelpers import HideableElementsGraphicsLayoutWidget, MplBasePlot, addSimTorqueLines 
from brace.UI.PlotConfiguration.ConfigurePlotHelpers import PyQTBasePlot, addKneeAnglePlot, addLegLegend
from brace.UI.PlotConfiguration.ConfigurePlotHelpers import addSimKneeAngleLines, addThresholdLegend, addThresholdLines
from brace.UI.PlotConfiguration.ConfigurePlotHelpers import addTorquePlot, getLeftLabelFontFormat, setGraphLayout, setPlotLayout
from brace.UI.PlotConfiguration.ConfigurePlotHelpers import SIM_LINE_WIDTH, LINE_WIDTH, LEFT_SUFFIX, RIGHT_SUFFIX
from brace.UI.example.GUIController import StandingUIConfiguration
from brace.UI.GraphContext import GraphContext
from brace.example.exoskeleton.ControlLogicLookup import ControlLogicEnum
from brace.example.exoskeleton.ControlLogic.Standing import Standing

class StandingPlotsPyQt(PyQTBasePlot):
    """
        This graph is used in both the simulator and the Main GUI for graphing values. This serves as the customized plots
        to be used the Standing Controller, storing relevant values under a GraphContext when using the factory function
        createGraphContext.
    """

    # Keywords that handle the threshold lines for Standing
    turnOffThreshold = "Off"
    turnOnThreshold = "On"
    leftTurnOffThreshold = f"{turnOffThreshold}{LEFT_SUFFIX}"
    leftTurnOnThreshold = f"{turnOnThreshold}{LEFT_SUFFIX}"
    rightTurnOffThreshold = f"{turnOffThreshold}{RIGHT_SUFFIX}"
    rightTurnOnThreshold = f"{turnOnThreshold}{RIGHT_SUFFIX}"
    kneeAngleKeywordsLR = [leftTurnOffThreshold, rightTurnOffThreshold, leftTurnOnThreshold, rightTurnOnThreshold]

    kneeAngleThresholdKeywords = ['turnOffThreshold', 'turnOnThreshold']
    kneeAngleThresholdKeywordsLR = [f"{angle}{leg}" for leg, angle in itertools.product(['L', 'R'], kneeAngleThresholdKeywords)]

    @staticmethod
    def createGraphContext(graphContexts: list[GraphContext], standingGraphToggleHorizontalLayout: QHBoxLayout, 
                           standingGraphWidget: HideableElementsGraphicsLayoutWidget, MAX_TIME_RANGE: float, 
                           initFileDefaults: dict[str, float], simulator: bool, *_: list) -> int:
        """
            Factory Function to create graph context (and plots) for the Standing plots with pyqtgraph. Returns the index of the 
            graph context.

            :params graphContexts: The list of GraphContexts to be used in the plots.
            :type graphContexts: list[GraphContext]
            :params standingGraphToggleHorizontalLayout: The Horizontal Layout to populate the checkboxes for hiding the graphs.
            :type standingGraphToggleHorizontalLayout: QHBoxLayout
            :params standingGraphWidget: The widget that contains the graphs.
            :type standingGraphWidget: HideableElementsGraphicsLayoutWidget
            :params MAX_TIME_RANGE: The time range that the graph should show on the x-axis.
            :type MAX_TIME_RANGE: float
            :params initFileDefaults: Defaults from the ini file that should be populated for thresholds.
            :type initFileDefaults: dict[str, float]
            :params simulator: A boolean determining whether or not this is from the simulator.
            :type simulator: bool

            :return: The index of the graph context.
            :rtype: int
        """
        
        defaults = dict(zip(StandingPlotsPyQt.kneeAngleThresholdKeywordsLR, [initFileDefaults['standingTurnOffThresholdSpinBox'], initFileDefaults['standingTurnOnThresholdSpinBox']] * 2)) 
        standingPlots = StandingPlotsPyQt(standingGraphWidget, MAX_TIME_RANGE = MAX_TIME_RANGE, 
                                          xGraphLim = MAX_TIME_RANGE, simulator = simulator, **defaults)
        fig, axes, axisLines = standingPlots.getFigureAxesAxesMapTriple()
        simAxisLines = standingPlots.getSimulatorAxisMaps()
        graphContexts.append(GraphContext(fig, axes, axisLines, simAxisLines,
                                          standingGraphToggleHorizontalLayout, 
                                          Standing,
                                          ControlLogicEnum.STANDING,
                                          StandingUIConfiguration.getStandingConfigurationChanges, 
                                          StandingUIConfiguration.validateStandingConfiguration, 
                                          StandingUIConfiguration.writeStandingConfigurationChanges, 
                                          StandingPlotsPyQt.resetStandingPlotAxis, 
                                          StandingUIConfiguration.readStandingConfigurationFromController,
                                          StandingUIConfiguration.readStandingConfigurationFromSaveFile,
                                          StandingUIConfiguration.adjustStandingPlotThresholdValues))
        return len(graphContexts) - 1

    def __init__(self, graphicsLayoutWidget: HideableElementsGraphicsLayoutWidget, simulator: bool, **kwargs):
        """
            Initializes the plots featuring knee angle and torque.

            :params graphicsLayoutWidget: The widget that should contain the graphs.
            :type graphicsLayoutWidget: HideableElementsGraphicsLayoutWidget
            :params simulator: A boolean determining whether or not the simulator lines should be drawn. Default is False.
            :type simulator: bool
            :params kwargs: Parameters that may be passed in for defaults such as values for threshold lines.
            :type kwargs: dict[str, Any]
        """

        super().__init__(graphicsLayoutWidget, simulator, **kwargs)
        xGraphLim = kwargs.get('xGraphLim', 10)
        axisLabelFont = getLeftLabelFontFormat()

        # Knee Angle Plot
        kneeAnglePlot, lineKneeAngleL, lineKneeAngleR = addKneeAnglePlot(self.fig, 0, xGraphLim = xGraphLim, axisLabelFont = axisLabelFont, lineFontSize = LINE_WIDTH)
        legLegend = addLegLegend(kneeAnglePlot, lineKneeAngleL, lineKneeAngleR)
        if self.simulator:
            lineSimKneeAngleL, lineSimKneeAngleR = addSimKneeAngleLines(kneeAnglePlot, SIM_LINE_WIDTH)

        colors = ['red', 'blueviolet']
        defaultAngleValues = [kwargs.get(keyword, 0) for keyword in StandingPlotsPyQt.kneeAngleThresholdKeywordsLR]
        leftThresholdNames = [StandingPlotsPyQt.leftTurnOffThreshold, StandingPlotsPyQt.leftTurnOnThreshold]
        rightThresholdNames = [StandingPlotsPyQt.rightTurnOffThreshold, StandingPlotsPyQt.rightTurnOnThreshold]

        linesAngle = addThresholdLines(kneeAnglePlot, defaultAngleValues, colors, leftThresholdNames, rightThresholdNames)
        angleLegend = addThresholdLegend(kneeAnglePlot, linesAngle)

        #Torque Plot
        torquePlot, lineDesiredRestrictionsL, lineDesiredRestrictionsR = addTorquePlot(self.fig, 1, axisLabelFont = axisLabelFont, lineFontSize = LINE_WIDTH)
        if self.simulator:
            lineSimDesiredRestrictionsL, lineSimDesiredRestrictionsR = addSimTorqueLines(torquePlot, SIM_LINE_WIDTH)
        
        plotsToUse = [kneeAnglePlot, torquePlot]
        self.axes = np.reshape(plotsToUse, shape = (graphicsLayoutWidget.centralWidget.layout.rowCount(), graphicsLayoutWidget.centralWidget.layout.columnCount()))
        setPlotLayout(self.axes)

        leftLineThresholds = [line for line in linesAngle if LEFT_SUFFIX in line._name]
        rightLineThresholds = [line for line in linesAngle if RIGHT_SUFFIX in line._name]
        leftLineEntries = [lineKneeAngleL, lineDesiredRestrictionsL]
        rightLineEntries = [lineKneeAngleR, lineDesiredRestrictionsR]
        
        if self.simulator:
            simLeftLineEntries = [lineSimKneeAngleL, lineSimDesiredRestrictionsL, *leftLineThresholds]
            simRightLineEntries = [lineSimKneeAngleR, lineSimDesiredRestrictionsR, *rightLineThresholds]
            self.fig.setSimLeftLineEntries(simLeftLineEntries, lineSimKneeAngleL)
            self.fig.setSimRightLineEntries(simRightLineEntries, lineSimKneeAngleR)
            simAxisLines: dict[str, PlotDataItem] = {'thetaL' : None,
                                                     'thetaR' : None,
                                                     'fsrL': None,
                                                     'fsrR': None,
                                                     'thetaDotWinL': None,
                                                     'thetaDotWinR': None,
                                                     'torqueDesL': None,
                                                     'torqueDesR': None,
                                                     'torqueInL' : lineSimDesiredRestrictionsL,
                                                     'torqueInR' : lineSimDesiredRestrictionsR }
            self.simAxisMaps = { Standing: simAxisLines }
        else:
            leftLineEntries.extend(leftLineThresholds)
            rightLineEntries.extend(rightLineThresholds)

        self.fig.legendsToHide = [legLegend] # Legends that should be hidden when pressing hotkey 'H'
        self.fig.setLeftLineEntries(leftLineEntries, lineKneeAngleL) # Lines to hide when pressing 'L'
        self.fig.setRightLineEntries(rightLineEntries, lineKneeAngleR) # Lines to hide when pressing 'R'

        axisLines: dict[str, PlotDataItem] = {'thetaL' : lineKneeAngleL,
                                        'thetaR' : lineKneeAngleR,
                                        'fsrL': None,
                                        'fsrR': None,
                                        'thetaDotWinL': None,
                                        'thetaDotWinR': None,
                                        'torqueDesL': None,
                                        'torqueDesR': None,
                                        'torqueInL' : lineDesiredRestrictionsL,
                                        'torqueInR' : lineDesiredRestrictionsR }
        
        self.axisMaps = { Standing: axisLines }
    
    @staticmethod
    def setThresholdValues(axes: np.ndarray[PlotItem], turnOffThreshold: int, turnOnThreshold: int, isLeft: bool) -> None:
        """
            Sets the threshold values on the knee angle plot for turn on and turn off triggers.

            :params axes: A numpy array that contains the PlotItems.
            :type axes: numpy.ndarray[PlotItem]
            :params turnOffThreshold: The threshold at which torque should be turned off (after sending torque for extension).
            :type turnOffThreshold: int
            :params turnOnThreshold: The threshold at which torque should be turned on, until it reaches the turn off threshold.
            :type turnOnThreshold: int
            :params isLeft: Whether or not the threshold value belongs to the left or right leg (to change the respective line).
            :type isLeft: bool

            :return: None
            :rtype: None
        """
        kneeAnglePlot = axes[0, 0]
        turnOffThresholdName = StandingPlotsPyQt.leftTurnOffThreshold if isLeft else StandingPlotsPyQt.rightTurnOffThreshold
        turnOnThresholdName = StandingPlotsPyQt.leftTurnOnThreshold if isLeft else StandingPlotsPyQt.rightTurnOnThreshold
        kneeAngleDictionary = { turnOffThresholdName: turnOffThreshold, turnOnThresholdName: turnOnThreshold }
        PyQTBasePlot.setThresholdLinesHelper(kneeAnglePlot, kneeAngleDictionary)

    @staticmethod
    def resetStandingPlotAxis(axes: np.ndarray[PlotItem], xGraphLim: int) -> None:
        """
            Sets the plots back to initialized values (run usually when the data streaming starts).

            :params axes: A numpy array of the PlotItems to be referenced from.
            :type axes: numpy.ndarray[PlotItem]
            :params xGraphLim: The limits for the x-axis (time). The plots will be drawn using this limit as the full span of the plots.
            :type xGraphLim: int

            :return: None
            :rtype: None
        """
        kneeAnglePlot = axes[0, 0]
        torquePlot = axes[1, 0]
        kneeAnglePlot.setRange(xRange = (-xGraphLim, 0), yRange = (-10, 80), padding = 0.05)
        torquePlot.setRange(yRange = (-10, 10), padding = 0.05)

class StandingPlotsMpl(MplBasePlot):
    """
        This graph is used for plotting values for the Standing controller using MatPlotLib plots, giving more
        of a publication-useful look and feel for the plots. This is not used for either simulation nor main GUI,
        only for opening datasets.
    """
        
    def __init__(self, matplotlibwidget: MatplotlibWidget, **kwargs):
        """
            Initializes the plots featuring knee angle and torque.

            :params matplotlibwidget: The widget that should contain the graphs.
            :type MatplotlibWidget: HideableElementsGraphicsLayoutWidget
            :params kwargs: Extra key-value parameters that may be used in initialization such as thresholds.
            :type kwargs: dict[str, Any]

            :return: None
            :rtype: None
        """
        super().__init__(matplotlibwidget, **kwargs)
        self.axes = self.fig.subplots(2, 1, squeeze = False, sharex = True)
        self.fig.subplots_adjust(hspace = 0.10, top = 0.99, bottom = 0.075, left = 0.05, right = 0.995)
        MplBasePlot.removeTickNumbers(self.axes)

        kneeAngleAxes: Axes = self.axes[0, 0]
        lineKneeAngleL, lineKneeAngleR = self.addKneeAnglePlot(kneeAngleAxes)
        kneeLegend = kneeAngleAxes.legend(loc = 'upper left')
        kneeLegend.set_draggable(True)
        
        #Torque Plot
        torqueAxes: Axes = self.axes[1, 0]
        lineDesiredL, lineDesiredR = self.addTorquePlot(torqueAxes)
        
        axisLines: dict[str, Line2D] = {'thetaL' : lineKneeAngleL,
                                        'thetaR' : lineKneeAngleR,
                                        'fsrL': None,
                                        'fsrR': None,
                                        'thetaDotWinL': None,
                                        'thetaDotWinR': None,
                                        'torqueDesL': None,
                                        'torqueDesR': None,
                                        'torqueInL' : lineDesiredL,
                                        'torqueInR' : lineDesiredR }
        
        self.setHideableLegends([kneeLegend])
        self.setHideableLines([lineKneeAngleL, lineDesiredL], [lineKneeAngleR, lineDesiredR])
        self.axisMaps = { Standing: axisLines }