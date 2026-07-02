import numpy as np
from PySide6.QtWidgets import QHBoxLayout
from pyqtgraph import PlotItem, GraphicsLayoutWidget, mkPen, GridItem, PlotDataItem

from brace.UI.PlotConfiguration.ConfigurePlotHelpers import PyQTBasePlot, getLeftLabelFontFormat, setPlotLayout
from brace.UI.GraphContext import GraphContext
from brace.example.zaber.ZaberControlLogic import ZaberData, ControlLogic
import brace.example.zaber.ProportionalUIConfiguration as ProportionalUIConfiguration

class ProportionalPlotsPyQt(PyQTBasePlot):

    def createGraphContext(graphContexts: list[GraphContext], proportionalGraphToggleHorizontalLayout: QHBoxLayout, 
                           proportionalGraphWidget: GraphicsLayoutWidget, MAX_TIME_RANGE: float, *_: list):

        """
            Factory Function to create graph context (and plots) for the Proportional plots with pyqtgraph. Returns the index of the 
            graph context.

            :params graphContexts: The list of GraphContexts to be used in the plots.
            :type graphContexts: list[GraphContext]
            :params proportionalGraphToggleHorizontalLayout: The Horizontal Layout to populate the checkboxes for hiding the graphs.
            :type proportionalGraphToggleHorizontalLayout: QHBoxLayout
            :params proportionalGraphWidget: The widget that contains the graphs.
            :type proportionalGraphWidget: HideableElementsGraphicsLayoutWidget
            :params MAX_TIME_RANGE: The time range that the graph should show on the x-axis.
            :type MAX_TIME_RANGE: float
            :return: The index of the graph context.
            :rtype: int
        """
        proportionalPlots = ProportionalPlotsPyQt(proportionalGraphWidget, MAX_TIME_RANGE = MAX_TIME_RANGE, xGraphLim = MAX_TIME_RANGE)
        fig, axes, axisLines = proportionalPlots.getFigureAxesAxesMapTriple()
        graphContexts.append(GraphContext(fig, 
                                          axes, 
                                          axisLines,
                                          None, # simulatorAxisLines
                                          proportionalGraphToggleHorizontalLayout, 
                                          ZaberData,
                                          ControlLogic.ZaberController,
                                          ProportionalUIConfiguration.getProportionalConfigurationChanges, 
                                                ProportionalUIConfiguration.validateProportionalConfiguration, 
                                                ProportionalUIConfiguration.writeProportionalConfigurationChanges, 
                                                ProportionalPlotsPyQt.resetProportionalPlotAxis, 
                                                ProportionalUIConfiguration.readProportionalConfigurationFromController,
                                                ProportionalUIConfiguration.readProportionalConfigurationFromSaveFile,
                                                ProportionalUIConfiguration.adjustProportionalPlotThresholdValues))
        return len(graphContexts) - 1

    def __init__(self, graphicsLayoutWidget: GraphicsLayoutWidget, **kwargs):
        """
            Initializes the plots for actuator position and the load cell value.

            :params graphicsLayoutWidget: The widget that should contain the graphs.
            :type graphicsLayoutWidget: HideableElementsGraphicsLayoutWidget
            :params kwargs: Parameters that may be passed in for defaults such as values for threshold lines.
            :type kwargs: dict[str, Any]

            :return: None
            :rtype: None
        """
        super().__init__(graphicsLayoutWidget, **kwargs)
        xGraphLim = kwargs.get('xGraphLim', 10)
        lineFontSize = 3
        axisLabelFont = getLeftLabelFontFormat()

        loadCellPlot = self.fig.addPlot(row = 0, col = 0, name = "Load Cell Plot", labels = {'left': "Force (g)", 'bottom': "t (s)" })
        lineLoadCell = loadCellPlot.plot([], [], pen = mkPen('mediumblue', width = lineFontSize), name = "forceValue", autodownsample = True, 
                                            downsampleMethod = 'subsample', clipToView = True, skipFiniteCheck = True)
        loadCellGrid = GridItem()
        loadCellGrid.setTickSpacing(x = [None, None], y = [-1.0, 15]) # Adding a negative value seems to remove the text labels.
        loadCellPlot.addItem(loadCellGrid)
        loadCellPlot.setRange(xRange = (-xGraphLim, 0), yRange = (-10, 500), padding = 0.05)
        loadCellPlot.getAxis('left').label.setFont(axisLabelFont)

        # Position Plot
        positionPlot = self.fig.addPlot(row = 1, col = 0, name = "Position Plot", labels = {'left': "Length (mm)", 'bottom': "t (s)" })
        linePosition = positionPlot.plot([], [], pen = mkPen('mediumblue', width = lineFontSize), 
                                                name = "Desired with Restrictions Left", autodownsample = True, downsampleMethod = 'subsample', 
                                                clipToView = True, skipFiniteCheck = True)
        positionGrid = GridItem()
        positionGrid.setTickSpacing(x = [None, None], y = [-1.0, 5.0])
        positionPlot.addItem(positionGrid)
        positionPlot.setRange(yRange = (-25, 75), padding = 0.05)
        positionPlot.setXLink("Load Cell Plot") # Moving the X scale also moves the Load cell plot scale and whatever also is linked to it
        positionPlot.getAxis('left').label.setFont(axisLabelFont)

        plotsToUse = [loadCellPlot, positionPlot]
        self.axes = np.reshape(plotsToUse, shape = (graphicsLayoutWidget.centralWidget.layout.rowCount(), graphicsLayoutWidget.centralWidget.layout.columnCount()))
        setPlotLayout(self.axes)

        axisLines: dict[str, PlotDataItem] = {'position' : linePosition,
                                        'loadcell': lineLoadCell}
        
        self.axisMaps = { ZaberData: axisLines }
    
    def resetProportionalPlotAxis(axes: np.ndarray[PlotItem], xGraphLim: int) -> None:
        """
            Resets the plots back to a given view.

            :param axes: Set of PlotItems whose plots should be altered.
            :type axes: numpy.ndarray[PlotItem]
            :param xGraphLim: Initialized limit of the X-axis value.
            :type xGraphLim: int
            :return: None
            :rtype: None
        """
        loadCellPlot = axes[0, 0]
        positionPlot = axes[1, 0]
        loadCellPlot.setRange(xRange = (-xGraphLim, 0), yRange = (-10, 500), padding = 0.05)
        positionPlot.setRange(yRange = (-25, 75), padding = 0.05)