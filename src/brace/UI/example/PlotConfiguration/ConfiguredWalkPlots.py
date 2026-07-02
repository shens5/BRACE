from typing import override
from matplotlib.axes import Axes
from matplotlib.lines import Line2D
import numpy as np
from PySide6.QtWidgets import QHBoxLayout
from pyqtgraph import mkPen, GridItem, PlotItem, PlotDataItem
from pyqtgraph.widgets.MatplotlibWidget import MatplotlibWidget
import itertools
from PySide6.QtCore import Qt
from brace.UI.PlotConfiguration.ConfigurePlotHelpers import HideableElementsGraphicsLayoutWidget, MplBasePlot, PyQTBasePlot, addFsrPlot, addSimStateLines 
from brace.UI.PlotConfiguration.ConfigurePlotHelpers import addKneeAnglePlot, addSimKneeAngleLines, addLegLegend, addSimTorqueLines 
from brace.UI.PlotConfiguration.ConfigurePlotHelpers import addTorquePlot, addWindowedAngularVelocityPlot, getLeftLabelFontFormat
from brace.UI.PlotConfiguration.ConfigurePlotHelpers import setPlotLayout, addThresholdLines, addThresholdLegend
from brace.UI.PlotConfiguration.ConfigurePlotHelpers import LEFT_COLOR, RIGHT_COLOR, SIM_LINE_WIDTH, LINE_WIDTH, LEFT_SUFFIX, RIGHT_SUFFIX
from brace.UI.example.PlotConfiguration import ConfiguredWalkPlots
from brace.UI.example.GUIController import WalkUIConfiguration
from brace.UI.GraphContext import GraphContext
from brace.example.exoskeleton.ControlLogicLookup import ControlLogicEnum
from brace.example.exoskeleton.ControlLogic.FSM import FSM5
from brace.Server.GPIOSynch.PushButton import Trigger

class WalkPlotsPyQt(PyQTBasePlot):
    # Velocity Threshold names
    thresholdEarlyMidStanceName = "ESt. to MSt."
    thresholdMidLateStanceName = "MSt. to LSt."
    thresholdEarlyLateSwingName = "ESw. to LSw."
    leftThresholdEarlyMidStanceName = f"{thresholdEarlyMidStanceName}{LEFT_SUFFIX}"
    rightThresholdEarlyMidStanceName = f"{thresholdEarlyMidStanceName}{RIGHT_SUFFIX}"
    leftThresholdMidLateStanceName = f"{thresholdMidLateStanceName}{LEFT_SUFFIX}"
    rightThresholdMidLateStanceName = f"{thresholdMidLateStanceName}{RIGHT_SUFFIX}"
    leftThresholdEarlyLateSwingName = f"{thresholdEarlyLateSwingName}{LEFT_SUFFIX}"
    rightThresholdEarlyLateSwingName = f"{thresholdEarlyLateSwingName}{RIGHT_SUFFIX}"

    # FSR Threshold names
    thresholdStanceName = "HS"
    thresholdSwingName = "TO"
    leftThresholdInitialContactName = f"{thresholdStanceName}{LEFT_SUFFIX}"
    leftThresholdSwingName = f"{thresholdSwingName}{LEFT_SUFFIX}"
    rightThresholdInitialContactName = f"{thresholdStanceName}{RIGHT_SUFFIX}"
    rightThresholdSwingName = f"{thresholdSwingName}{RIGHT_SUFFIX}"

    velocityKeywords = ['velocityEarlyToMidStanceThreshold', 'velocityMidToLateStanceThreshold', 'velocityEarlyToLateSwingThreshold']
    velocityKeywordsLR = [f"{velocity}{leg}" for leg, velocity in itertools.product(['L', 'R'], velocityKeywords)]
    thresholdKeywords = ['forceSensorThresholdInitialContact', 'forceSensorThresholdSwing']
    thresholdKeywordsLR = [f"{force}{leg}" for leg, force in itertools.product(['L', 'R'], thresholdKeywords)]

    @staticmethod
    def createGraphContext(graphContexts: list[GraphContext], walkFSM5GraphToggleHorizontalLayout: QHBoxLayout, 
                           walkFSM5GraphWidget: HideableElementsGraphicsLayoutWidget, MAX_TIME_RANGE: float, 
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
        thresholdList = [initFileDefaults['walkFSM5EarlyToMidStanceThresholdSpinBox'],
                         initFileDefaults['walkFSM5MidToLateStanceThresholdSpinBox'],
                         initFileDefaults['walkFSM5EarlyToLateSwingThresholdSpinBox']] * 2 + [initFileDefaults['walkFSM5IcThresholdSpinBox'],
                         initFileDefaults['walkFSM5ToThresholdSpinBox']] * 2
        walkKeywords = dict(zip(WalkPlotsPyQt.velocityKeywordsLR + WalkPlotsPyQt.thresholdKeywordsLR, thresholdList))
        walkPlots = WalkPlotsPyQt(walkFSM5GraphWidget, MAX_TIME_RANGE = MAX_TIME_RANGE, xGraphLim = MAX_TIME_RANGE, simulator = simulator, **walkKeywords)
        fig, axes, axisLines = walkPlots.getFigureAxesAxesMapTriple()
        simulatorAxisLines = walkPlots.getSimulatorAxisMaps()
        graphContexts.append(GraphContext(fig, axes, axisLines, simulatorAxisLines, 
                                          walkFSM5GraphToggleHorizontalLayout, 
                                          FSM5,
                                          ControlLogicEnum.FSM5,
                                          WalkUIConfiguration.getWalkConfigurationChanges, 
                                          WalkUIConfiguration.validateWalkConfiguration, 
                                          WalkUIConfiguration.writeWalkConfigurationChanges, 
                                          ConfiguredWalkPlots.WalkPlotsPyQt.resetWalkPlotAxis, 
                                          WalkUIConfiguration.readWalkConfigurationFromController,
                                          WalkUIConfiguration.readWalkConfigurationFromSaveFile,
                                          WalkUIConfiguration.adjustWalkPlotThresholdValues))
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

            :return: None
            :rtype: None
        """

        super().__init__(graphicsLayoutWidget, simulator, **kwargs)
        xGraphLim = kwargs.get('xGraphLim', 10)
        axisLabelFont = getLeftLabelFontFormat()

        # Knee Angle Plot
        kneeAnglePlot, lineKneeAngleL, lineKneeAngleR = addKneeAnglePlot(self.fig, row = 0, xGraphLim = xGraphLim,
                                                                         axisLabelFont = axisLabelFont, lineFontSize = LINE_WIDTH)
        
        legLegend = addLegLegend(kneeAnglePlot, lineKneeAngleL, lineKneeAngleR)
        
        # These lines aren't actually filled. They are to designate what they are. Only the outputs drawn
        if self.simulator:
            lineSimKneeAngleL, lineSimKneeAngleR = addSimKneeAngleLines(kneeAnglePlot, SIM_LINE_WIDTH)
            # Legend entries are filled automatically.

        # Angular Velocity Plot
        windowedAngularVelocityPlot, lineWindowedAngularVelocityL, lineWindowedAngularVelocityR = addWindowedAngularVelocityPlot(self.fig,
                                                                                                                                 row = 1,
                                                                                                                                 axisLabelFont = axisLabelFont, 
                                                                                                                                 lineFontSize = LINE_WIDTH)
        # Velocity Threshold lines
        colors = ['red', 'yellow', 'blue']
        
        defaultVelocityValues = [kwargs.get(keyword, 0) for keyword in WalkPlotsPyQt.velocityKeywordsLR]
        leftThresholdNames = [WalkPlotsPyQt.leftThresholdEarlyMidStanceName, WalkPlotsPyQt.leftThresholdMidLateStanceName, WalkPlotsPyQt.leftThresholdEarlyLateSwingName]
        rightThresholdNames = [WalkPlotsPyQt.rightThresholdEarlyMidStanceName, WalkPlotsPyQt.rightThresholdMidLateStanceName, WalkPlotsPyQt.rightThresholdEarlyLateSwingName]

        linesVelocity = addThresholdLines(windowedAngularVelocityPlot, defaultVelocityValues, colors, leftThresholdNames, rightThresholdNames)
        velocityLegend = addThresholdLegend(windowedAngularVelocityPlot, linesVelocity)

        #FSR Plot
        fsrPlot, lineFsrL, lineFsrR = addFsrPlot(self.fig, row = 2, axisLabelFont = axisLabelFont, lineFontSize = LINE_WIDTH)

        colors = ['red', 'blueviolet']
        defaultThresholdValues = [kwargs.get(keyword, 0) for keyword in WalkPlotsPyQt.thresholdKeywordsLR]
        leftThresholdNames = [WalkPlotsPyQt.leftThresholdInitialContactName, WalkPlotsPyQt.leftThresholdSwingName]
        rightThresholdNames = [WalkPlotsPyQt.rightThresholdInitialContactName, WalkPlotsPyQt.rightThresholdSwingName]

        # Two static infinite lines that stretch out based on the value.
        # Background of the legend is slightly transparent. Legend is offset to the top right.
        linesFsr = addThresholdLines(fsrPlot, defaultThresholdValues, colors, leftThresholdNames, rightThresholdNames)
        fsrLegend = addThresholdLegend(fsrPlot, linesFsr)

        #Torque Plot
        torquePlot, lineDesiredRestrictionsL, lineDesiredRestrictionsR = addTorquePlot(self.fig, 3, axisLabelFont = axisLabelFont, lineFontSize = LINE_WIDTH)
        if self.simulator:
            lineSimDesiredRestrictionsL, lineSimDesiredRestrictionsR = addSimTorqueLines(torquePlot, SIM_LINE_WIDTH)

        #State Plot
        yTicks = [0, 1, 2, 3, 4, 5, 6]
        yLabel = ["Waiting", "Est", "Mst", "Lst", "Esw", "Lsw", ""]

        statePlot = self.fig.addPlot(row = 4, col = 0, name = "State Plot", labels = {'left': "FSM", 'bottom': "t (s)" })
        lineStateL = statePlot.plot([], [], pen = mkPen(LEFT_COLOR, width = LINE_WIDTH), name = "stateLeft", 
                                    autodownsample = True, downsampleMethod = 'subsample', clipToView = True, skipFiniteCheck = True)
        lineStateR = statePlot.plot([], [], pen = mkPen(RIGHT_COLOR, width = LINE_WIDTH), name = "stateRight", 
                                    autodownsample = True, downsampleMethod = 'subsample', clipToView = True, skipFiniteCheck = True)
        stateGrid = GridItem()
        stateGrid.setTickSpacing(x = [None, None], y = [-1.0, 1.0])
        statePlot.addItem(stateGrid)
        statePlot.setRange(yRange = (0, 6), padding = 0.00)
        statePlot.setXLink("Knee Angle Plot") # Moving the X scale also moves the Knee Angle Plot scale and whatever also is linked to it.
        leftAxis = statePlot.getAxis('left')
        leftAxis.setTicks([list(zip(yTicks, yLabel))])
        statePlot.getAxis('left').label.setFont(axisLabelFont)

        if self.simulator:
            lineSimStateL, lineSimStateR = addSimStateLines(statePlot, SIM_LINE_WIDTH)

        plotsToUse = [kneeAnglePlot, windowedAngularVelocityPlot, fsrPlot, torquePlot, statePlot]

        self.axes = np.reshape(plotsToUse, shape = (graphicsLayoutWidget.centralWidget.layout.rowCount(), graphicsLayoutWidget.centralWidget.layout.columnCount()))
        setPlotLayout(self.axes)
        self.fig.setLegendEntries([legLegend, fsrLegend, velocityLegend]) # Legends that should be hidden when pressing hotkey 'H'

        thresholdLinesLeft = [*[line for line in linesVelocity if LEFT_SUFFIX in line._name],
                                  *[line for line in linesFsr if LEFT_SUFFIX in line._name]]
        thresholdLinesRight = [*[line for line in linesVelocity if RIGHT_SUFFIX in line._name], 
                                  *[line for line in linesFsr if RIGHT_SUFFIX in line._name]]
        leftLineEntries = [lineKneeAngleL, lineWindowedAngularVelocityL, lineFsrL, lineDesiredRestrictionsL, lineStateL]
        rightLineEntries = [lineKneeAngleR, lineWindowedAngularVelocityR, lineFsrR, lineDesiredRestrictionsR, lineStateR]
        
        if self.simulator: # If simulation, then the threshold lines belong to the simulation
            simLeftLineEntries = [lineSimKneeAngleL, lineSimStateL, lineSimDesiredRestrictionsL, *thresholdLinesLeft]
            simRightLineEntries = [lineSimKneeAngleR, lineSimStateR, lineSimDesiredRestrictionsR, *thresholdLinesRight]
            self.fig.setSimLeftLineEntries(simLeftLineEntries, lineSimKneeAngleL)
            self.fig.setSimRightLineEntries(simRightLineEntries, lineSimKneeAngleR)
            simAxisLines: dict[str, PlotDataItem] = { 'thetaL' : None,
                                                    'thetaR' : None,
                                                    'thetaDotWinL' : None,
                                                    'thetaDotWinR' : None,
                                                    'fsrL' : None,
                                                    'fsrR' : None,
                                                    'stateL' : lineSimStateL,
                                                    'stateR' : lineSimStateR,
                                                    'torqueDesL' : None,
                                                    'torqueDesR' : None,
                                                    'torqueInL' : lineSimDesiredRestrictionsL,
                                                    'torqueInR' : lineSimDesiredRestrictionsR }
            self.simAxisMaps = { FSM5: simAxisLines }
        else: # Otherwise they belong to the online lines.
            leftLineEntries.extend(thresholdLinesLeft)
            rightLineEntries.extend(thresholdLinesRight)
            
        self.fig.setLeftLineEntries(leftLineEntries, lineKneeAngleL) # Lines to hide when pressing 'L'
        self.fig.setRightLineEntries(rightLineEntries, lineKneeAngleR) # Lines to hide when pressing 'R'
        axisLines: dict[str, PlotDataItem] = { 'thetaL' : lineKneeAngleL,
                                        'thetaR' : lineKneeAngleR,
                                        'thetaDotWinL' : lineWindowedAngularVelocityL,
                                        'thetaDotWinR' : lineWindowedAngularVelocityR,
                                        'fsrL' : lineFsrL,
                                        'fsrR' : lineFsrR,
                                        'stateL' : lineStateL,
                                        'stateR' : lineStateR,
                                        'torqueDesL' : None,
                                        'torqueDesR' : None,
                                        'torqueInL' : lineDesiredRestrictionsL,
                                        'torqueInR' : lineDesiredRestrictionsR }
        triggerAxisLines: dict[str, PlotDataItem] = { 'triggerState' : None }
        self.axisMaps = { FSM5: axisLines, Trigger: triggerAxisLines }

    @staticmethod
    def setThresholdValues(axes: np.ndarray[PlotItem], velocityEarlyToMidStanceThreshold: float, velocityMidToLateStanceThreshold: float, velocityEarlyToLateSwingThreshold: float,
                           forceSensorThresholdInitialContact: float, forceSensorThresholdSwing: float, isLeft: bool) -> None:
        """
            Sets the threshold values on the angular velocity and FSR for state transitions.

            :params axes: A numpy array that contains the PlotItems.
            :type axes: numpy.ndarray[PlotItem]
            :params velocityEarlyToMidStanceThreshold: The threshold at which velocity should change the state from early to mid stance.
            :type velocityEarlyToMidStanceThreshold: float
            :params velocityMidToLateStanceThreshold: The threshold at which velocity should change the state from mid to late stance.
            :type velocityMidToLateStanceThreshold: float
            :params velocityEarlyToLateSwingThreshold: The threshold at which velocity should change the state from early to late swing.
            :type velocityEarlyToLateSwingThreshold: float
            :params forceSensorThresholdInitialContact: The threshold for the FSR that determines the stance phase.
            :type forceSensorThresholdInitialContact: float
            :params forceSensorThresholdSwing: The threshold for the FSR that determines the swing phase.
            :type forceSensorThresholdSwing: float
            :params isLeft: Whether or not the threshold value belongs to the left or right leg (to change the respective line).
            :type isLeft: bool

            :return: None
            :rtype: None
        """
        windowedAngularVelocityPlot = axes[1, 0]
        thresholdEarlyMidStanceName = WalkPlotsPyQt.leftThresholdEarlyMidStanceName if isLeft else WalkPlotsPyQt.rightThresholdEarlyMidStanceName
        thresholdMidLateStanceName = WalkPlotsPyQt.leftThresholdMidLateStanceName if isLeft else WalkPlotsPyQt.rightThresholdMidLateStanceName
        thresholdEarlyLateSwingName = WalkPlotsPyQt.leftThresholdEarlyLateSwingName if isLeft else WalkPlotsPyQt.rightThresholdEarlyLateSwingName
        windowedAngularVelocityDictionary = {thresholdEarlyMidStanceName: velocityEarlyToMidStanceThreshold, thresholdMidLateStanceName: velocityMidToLateStanceThreshold,
                                             thresholdEarlyLateSwingName: velocityEarlyToLateSwingThreshold}
        PyQTBasePlot.setThresholdLinesHelper(windowedAngularVelocityPlot, windowedAngularVelocityDictionary)

        fsrPlot = axes[2, 0]
        thresholdInitialContactName = WalkPlotsPyQt.leftThresholdInitialContactName if isLeft else WalkPlotsPyQt.rightThresholdInitialContactName
        thresholdSwingName = WalkPlotsPyQt.leftThresholdSwingName if isLeft else WalkPlotsPyQt.rightThresholdSwingName
        fsrThresholdDictionary = {thresholdInitialContactName: forceSensorThresholdInitialContact, thresholdSwingName: forceSensorThresholdSwing}
        PyQTBasePlot.setThresholdLinesHelper(fsrPlot, fsrThresholdDictionary)

    @staticmethod
    def resetWalkPlotAxis(axes: np.ndarray[PlotItem], xGraphLim: int) -> None:
        """
            Resets the axis plot for walking to initialized values.
            
            :params axes: A numpy array that contains the PlotItems.
            :type axes: numpy.ndarray[PlotItem]
            :params xGraphLim: The limits for the x-axis (time). The plots will be drawn using this limit as the full span of the plots.
            :type xGraphLim: int

            :return: None
            :rtype: None
        """
        kneeAnglePlot = axes[0, 0]
        windowedAngularVelocityPlot = axes[1, 0]
        fsrPlot = axes[2, 0]
        torquePlot = axes[3, 0]
        statePlot = axes[4, 0]
        kneeAnglePlot.setRange(xRange = (-xGraphLim, 0), yRange = (-10, 80), padding = 0.05)
        windowedAngularVelocityPlot.setRange(yRange = (-200, 200), padding = 0.00)
        fsrPlot.setRange(yRange = (0, 9500), padding = 0.00)
        torquePlot.setRange(yRange = (-10, 10), padding = 0.05)
        statePlot.setRange(yRange = (0, 6), padding = 0.00)

class WalkPlotsMpl(MplBasePlot):
    """
        This graph is used for plotting values for the Walking controller using MatPlotLib plots, giving more
        of a publication-useful look and feel for the plots. This is not used for either simulation nor main GUI,
        only for opening datasets.
    """

    def __init__(self, matplotlibwidget: MatplotlibWidget, **kwargs):
        """
            Initializes the plots featuring knee angle, angular velocity, FSR, torque, and state.

            :params matplotlibwidget: The widget that should contain the graphs.
            :type MatplotlibWidget: HideableElementsGraphicsLayoutWidget
            :params kwargs: Extra key-value parameters that may be used in initialization such as thresholds.
            :type kwargs: dict[str, Any]

            :return: None
            :rtype: None
        """
        super().__init__(matplotlibwidget, **kwargs)
        self.fig = matplotlibwidget.canvas.figure
        self.axes = self.fig.subplots(5, 1, squeeze = False, sharex=True)
        self.fig.subplots_adjust(hspace = 0.10, top = 0.99, bottom = 0.075, left = 0.075, right = 0.995)
        MplBasePlot.removeTickNumbers(self.axes)

        #RECORDED DATA
        kneeAngleAxes: Axes = self.axes[0, 0]
        lineKneeAngleL, lineKneeAngleR = self.addKneeAnglePlot(kneeAngleAxes)
        kneeLegend = kneeAngleAxes.legend(loc = 'upper left')
        kneeLegend.set_draggable(True)

        #Windowed Angular Velocity Plot
        windowedAngularVelocityAxes: Axes = self.axes[1, 0]
        lineWindowedAngularVelocityL, lineWindowedAngularVelocityR = self.addWindowedAngularVelocityPlot(windowedAngularVelocityAxes)

        colors = ['red', 'yellow', 'blue']
        labels = ['ESt. to MSt. Thr.', 'MSt. to LSt. Thr.', 'ESw. to LSw. Thr.']
        thresholdNamesL = ['velocityEarlyToMidStanceThresholdL', 'velocityMidToLateStanceThresholdL', 'velocityEarlyToLateSwingThresholdL']
        thresholdNamesR = ['velocityEarlyToMidStanceThresholdR', 'velocityMidToLateStanceThresholdR', 'velocityEarlyToLateSwingThresholdR']
        leftVelocityHorizontalLines = MplBasePlot.addThresholdLines(windowedAngularVelocityAxes, colors, labels, thresholdNamesL, True, **kwargs)
        rightVelocityHorizontalLines = MplBasePlot.addThresholdLines(windowedAngularVelocityAxes, colors, labels, thresholdNamesR, False, **kwargs)
        angularVelocityHorizontalLines: list[Line2D] = [*leftVelocityHorizontalLines, *rightVelocityHorizontalLines]
            
        # Add velocity threshold legend and pick events.
        velocityLegend, velocityLinesByLabel = self.addPickableLegend(windowedAngularVelocityAxes, angularVelocityHorizontalLines)
        self.addOnPickEvent(velocityLegend, velocityLinesByLabel)

        #FSR Plot
        fsrAxes: Axes = self.axes[2, 0]
        lineFsrL, lineFsrR = self.addFsrPlot(fsrAxes)
        
        colors = ['red', 'blueviolet']
        labels = ['St. Thr.', 'Sw. Thr.']
        thresholdNamesL = ['forceSensorThresholdInitialContactL', 'forceSensorThresholdSwingL']
        thresholdNamesR = ['forceSensorThresholdInitialContactR', 'forceSensorThresholdSwingR']
        fsrLeftHorizontalLines = MplBasePlot.addThresholdLines(fsrAxes, colors, labels, thresholdNamesL, True, **kwargs)
        fsrRightHorizontalLines = MplBasePlot.addThresholdLines(fsrAxes, colors, labels, thresholdNamesR, False, **kwargs)
        fsrHorizontalLines = [*fsrLeftHorizontalLines, *fsrRightHorizontalLines]

        # Add FSR Legend and the pick events that allow hiding the horizontal lines.
        legend, linesByLabel = self.addPickableLegend(fsrAxes, fsrHorizontalLines)
        self.addOnPickEvent(legend, linesByLabel)

        #Torque Plot
        torqueAxes: Axes = self.axes[3, 0]
        lineDesiredRestrictionsL, lineDesiredRestrictionsR = self.addTorquePlot(torqueAxes)

        #State Plot
        yTicks = [0, 1, 2, 3, 4, 5, 6]
        yLabel = ["Waiting", "Est", "Mst", "Lst", "Esw", "Lsw", ""]

        stateAxes: Axes = self.axes[4, 0]
        lineStateL, = stateAxes.plot([], [], label = "Left",  animated = False)
        lineStateR, = stateAxes.plot([], [], label = "Right",  animated = False)
        stateAxes.set_ylim(0, 5)
        stateAxes.set_ylabel("FSM")
        stateAxes.set_yticks(yTicks)
        stateAxes.set_yticklabels(yLabel)
        stateAxes.grid(True)
        stateAxes.set_xlim(left = 0, right = 10)
        stateAxes.set_ylim(bottom = 0, top = 6)

        # Keep list of lines that need to be updated. This is a subset of all lines that are plotted.
        axisLines: dict[str, Line2D] = {'thetaL' : lineKneeAngleL,
                                        'thetaR' : lineKneeAngleR,
                                        'thetaDotWinL' : lineWindowedAngularVelocityL,
                                        'thetaDotWinR' : lineWindowedAngularVelocityR,
                                        'fsrL' : lineFsrL,
                                        'fsrR' : lineFsrR,
                                        'stateL' : lineStateL,
                                        'stateR' : lineStateR,
                                        'torqueDesL' : None,
                                        'torqueDesR' : None,
                                        'torqueInL' : lineDesiredRestrictionsL,
                                        'torqueInR' : lineDesiredRestrictionsR }
        
        self.setHideableLegends([kneeLegend, velocityLegend, legend])
        self.setHideableLines([lineKneeAngleL, lineWindowedAngularVelocityL, lineFsrL, lineStateL, 
                               lineDesiredRestrictionsL, *leftVelocityHorizontalLines, *fsrLeftHorizontalLines], 
                              [lineKneeAngleR, lineWindowedAngularVelocityR, lineFsrR, lineStateR, 
                               lineDesiredRestrictionsR, *rightVelocityHorizontalLines, *fsrRightHorizontalLines])
        self.axisMaps = { FSM5: axisLines }

    @override
    def updateFinalPlotMatplotlib(self, **kwargs) -> None:
        """
            Updates the final plots for the states to be fixed to -1 and 7.
        """
        stateAxes: Axes = self.axes[4, 0]
        stateAxes.set_ylim(bottom = -1.0, top = 7)