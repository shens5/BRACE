from abc import abstractmethod
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.legend import Legend
from matplotlib.lines import Line2D
import numpy as np
from pyqtgraph import GraphicsLayoutWidget, QtGui, mkPen, QtCore, PlotItem, PlotDataItem, LegendItem, mkBrush, mkColor, GridItem, ItemSample
from PySide6.QtWidgets import QSizePolicy
from pyqtgraph.widgets.MatplotlibWidget import MatplotlibWidget
from PySide6.QtCore import Qt
from bidict import bidict

# import pyqtgraph as pg
# pg.setConfigOptions(antialias = True) # Enable to remove aliasing (jagged lines)

LEFT_COLOR = "#FFAE00"
RIGHT_COLOR = "#1900FE"
SIM_LINE_WIDTH = 2
LINE_WIDTH = 2
LEFT_SUFFIX = '-L'
RIGHT_SUFFIX = '-R'

class HideableElementsGraphicsLayoutWidget(GraphicsLayoutWidget):
    """
        A GraphicsLayoutWidget subclass that allows for legend
        elements to be hidden with L and R for the legs.
    """

    def __init__(self, parent=None, show=False, size=None, title=None, **kargs):
        super().__init__(parent, show, size, title, **kargs)
        self.sizePolicy().setRetainSizeWhenHidden(True)
        self.leftLegToHide: list[PlotDataItem] = []
        self.rightLegToHide: list[PlotDataItem] = []
        self.simLeftLegToHide: list[PlotDataItem] = []
        self.simRightLegToHide: list[PlotDataItem] = []

        self.legendsToHide: list[LegendItem] = []
        self.leftLineFromLegend: PlotDataItem = None
        self.rightLineFromLegend: PlotDataItem = None
        self.simLeftLineFromLegend: PlotDataItem = None
        self.simRightLineFromLegend: PlotDataItem = None
        self.scene().sigMouseClicked.connect(self.toggleAllFromLegend)

    def _updateLegends(self) -> None: 
        """ For some reason, legends do not update when you hide using the setVisible on the lines automatically.
            A workaround to this is to just reset the visibility twice to force the update. Note that it has to do it twice,
            setting the visibility to its current visible state does not update the legend. """
        legend: LegendItem
        for legend in self.legendsToHide:
            updateLegend(legend)
    
    def toggleAllFromLegend(self, event: QtGui.QMouseEvent) -> None:
        """
            Toggles all of the lines from the legend. All of the respective lines
            will be toggled when the legend point is clicked.

            :param event: The event containing a leg element where all leg elements should be toggled together.
            :type event: QtGui.QMouseEvent
            :return: None
            :rtype: None
        """
        items = self.scene().items(event.scenePos())
        for item in items:
            if isinstance(item, ItemSample) and isinstance(item.item, PlotDataItem):
                if item.item is self.leftLineFromLegend:
                    self.toggleLeftLegs(item.item.isVisible())
                elif item.item is self.rightLineFromLegend:
                    self.toggleRightLegs(item.item.isVisible())
                elif item.item is self.simLeftLineFromLegend:
                    self.toggleSimLeftLegs(item.item.isVisible())
                elif item.item is self.simRightLineFromLegend:
                    self.toggleSimRightLegs(item.item.isVisible())

    def setLegendEntries(self, legendsToHide: list[LegendItem]) -> None:
        """
            Sets in the legend items to hide when the "H" hotkey is pressed
            
            :param legendsToHide: The legend items that should be hidden.
            :type legendsToHide: list[LegendItem]
            :return: None
            :rtype: None 
        """
        self.legendsToHide.extend(legendsToHide)

    def setLeftLineEntries(self, leftLineEntries: list[PlotDataItem], leftLineFromLegend: PlotDataItem = None) -> None:
        """
            Sets in the left line entries that should be hidden when "L" is pressed or the legend item is toggled.
            
            :param leftLineEntries: List of lines that should be toggled together.
            :type leftLineEntries: list[PlotDataItem]
            :param leftLineFromLegend: The line (from a legend) that dictates how the linked lines are toggled together.
            :type leftLineFromLegend: PlotDataItem

            :return: None
            :rtype: None
        """
        self.leftLegToHide.extend(leftLineEntries)
        self.leftLineFromLegend = leftLineFromLegend

    def setRightLineEntries(self, rightLineEntries: list[PlotDataItem], rightLineFromLegend: PlotDataItem = None) -> None:
        """
            Sets in the right line entries that should be hidden when "R" is pressed or the legend item is toggled.
            
            :param rightLineEntries: List of lines that should be toggled together.
            :type rightLineEntries: list[PlotDataItem]
            :param rightLineFromLegend: The line (from a legend) that dictates how the linked lines are toggled together.
            :type rightLineFromLegend: PlotDataItem

            :return: None
            :rtype: None
        """
        self.rightLegToHide.extend(rightLineEntries)
        self.rightLineFromLegend = rightLineFromLegend

    def setSimLeftLineEntries(self, simLeftLineEntries: list[PlotDataItem], simLeftLineFromLegend: PlotDataItem = None) -> None:
        """
            Sets in the left line simulator entries, which are a subset of lines that are hidden together, but should
            be hidden together.

            :param simLeftLineEntries: List of left simulator lines.
            :type simLeftLineEntries: list[PlotDataItem]
            :param simLeftLineFromLegend: The line from the legend that should toggle visibility of the simulator lines.
            :type simLeftLineFromLegend: PlotDataItem

            :return: None
            :rtype: None
        """
        self.simLeftLegToHide.extend(simLeftLineEntries)
        self.simLeftLineFromLegend = simLeftLineFromLegend
    
    def setSimRightLineEntries(self, simRightLineEntries: list[PlotDataItem], simRightLineFromLegend: PlotDataItem = None) -> None:
        """
            Sets in the right line simulator entries, which are a subset of lines that are hidden together, but should
            be hidden together.

            :param simRightLineEntries: List of left simulator lines.
            :type simRightLineEntries: list[PlotDataItem]
            :param simRightLineFromLegend: The line from the legend that should toggle visibility of the simulator lines.
            :type simRightLineFromLegend: PlotDataItem

            :return: None
            :rtype: None
        """
        self.simRightLegToHide.extend(simRightLineEntries)
        self.simRightLineFromLegend = simRightLineFromLegend

    def toggleLeg(self, lineFromLegend: PlotDataItem, legToHide: list[PlotDataItem], visible: bool = None) -> bool:
        """
            Helper function that toggles the lines visibility based on the first element.

            :param lineFromLegend: The line from the legend whose line visibility serves as the basis for the rest of the lines.
            :type lineFromLegend: PlotDataItem
            :param legToHide: The list of lines whose line visibility should be toggled.
            :type legToHide: list[PlotDataItem]
            :param visible: Whether or not the line should be visible. None indicates true toggling based on previous state.
            :type visible: bool

            :return: Whether or not the leg was set to visible or hidden.
            :rtype: bool
        """
        if legToHide:
            visible = not lineFromLegend.isVisible() if visible is None else visible # Base the visibility on the first element.
            for legLines in legToHide:
                legLines.setVisible(visible)
            self._updateLegends()
            return visible
        return False

    def toggleLeftLegs(self, visible: bool = None) -> bool:
        return self.toggleLeg(self.leftLineFromLegend, self.leftLegToHide, visible = visible)

    def toggleRightLegs(self, visible: bool = None) -> bool:
        return self.toggleLeg(self.rightLineFromLegend, self.rightLegToHide, visible = visible)

    def toggleSimLeftLegs(self, visible: bool = None) -> bool:
        return self.toggleLeg(self.simLeftLineFromLegend, self.simLeftLegToHide, visible = visible)

    def toggleSimRightLegs(self, visible: bool = None) -> bool:
        return self.toggleLeg(self.simRightLineFromLegend, self.simRightLegToHide, visible = visible)

    def keyPressEvent(self, ev: QtGui.QKeyEvent) -> None:
        """
            Toggles the visibility of the legend if H is pressed, Left legs
            when L is pressed, and Right legs when R is pressed. Simulator legs are
            also included when available.

            :param ev: The event for the GraphicsLayoutWidget
            :type ev: QtGui.QKeyEvent
            :return: None
            :rtype: None
        """
        if ev.key() == QtCore.Qt.Key.Key_H:
            if hasattr(self, "legendsToHide"):
                for legend in self.legendsToHide:
                    legend.setVisible(not legend.isVisible())
        elif ev.key() == QtCore.Qt.Key.Key_L:
            # Hide the left lines and update the legends.
            leftLegVisibility = self.toggleLeftLegs()
            self.toggleSimLeftLegs(leftLegVisibility)
        elif ev.key() == QtCore.Qt.Key.Key_R:
            # Hide the right lines and update the legends.
            rightLegVisibility = self.toggleRightLegs()
            self.toggleSimRightLegs(rightLegVisibility)
        super().keyPressEvent(ev) # Call the base class implementation for default handling

class PyQTBasePlot():
    def __init__(self, graphicsLayoutWidget: HideableElementsGraphicsLayoutWidget, simulator: bool = False, **kwargs):
        """
            A subsuming object that contains the HideableElementsGraphicsLayoutWidget that contains
            some related information. Plot objects should subclass this object and define
            factory methods that define the GraphContext for each controller.
        
            :param graphicsLayoutWidget: The widget in the plot where the plots should be created.
            :type graphicsLayoutWidget: HideableElementsGraphicsLayoutWidget
            :param simulator: A boolean determining whether or not this is a graph being used by the simulator.
            :type simulator: bool
        """
        self.fig = graphicsLayoutWidget
        self.simulator = simulator
        self.simAxisMaps = {}
        setGraphLayout(self.fig)

    def setThresholdLinesHelper(plot: PlotItem, thresholdLineReplacement: dict[str, float]) -> None:
        for infiniteLine in plot.items:
            if "_name" in infiniteLine.__dict__: # Looking for PlotDataItems
                thresholdValue = thresholdLineReplacement.get(infiniteLine._name, None)
                if thresholdValue is not None:
                    infiniteLine.setValue(thresholdValue)

    def getFigureAxesAxesMapTriple(self) -> tuple[HideableElementsGraphicsLayoutWidget, list[PlotItem], dict[type, dict[str, PlotDataItem]]]:
        """
            Returns the triple containing the widget, the plots, and map of maps with the lines.
            Namely the axisMaps is referenced by type, then by attribute name for each line.

            :return: Tuple containing the figure widget, the plots, and the lines for the relevant attributes for the NamedTuple datatype.
            :rtype: tuple[HideableElementsGraphicsLayoutWidget, list[PlotItem], dict[type, dict[str, PlotDataItem]]]
        """
        return self.fig, self.axes, self.axisMaps
    
    def toggleLeftLines(self, visible: bool) -> None:
        """
            Toggles the left lines based on the desired visibility. Contains the simulator lines.
            :param visible: Whether or not the left lines should be visible.
            :type visible: bool
            :return: None
            :rtype: None
        """
        self.fig.toggleLeftLegs(visible)

    def toggleRightLines(self, visible: bool) -> None:
        """
            Toggles the right lines based on the desired visibility. Contains the simulator lines.
            :param visible: Whether or not the right lines should be visible.
            :type visible: bool
            :return: None
            :rtype: None
        """
        self.fig.toggleRightLegs(visible)
    
    def getSimulatorAxisMaps(self) -> dict[type, dict[str, PlotDataItem]]:
        """
            Gets specifically the simulator lines addressed first by type then by NamedTuple attributes.

            :return: The dictionary of types, which contains a dictionary of lines referenced by attribute names.
            :rtype: dict[type, dict[str, PlotDataItem]]
        """
        return self.simAxisMaps

class MplBasePlot():
    """
        Wrapping object for the Matplotlib-based plots for opening the files in the file viewer.
        Objects should similarly subclass this object for added functionality over the
        MatplotlibWidget (provided by pyqtgraph).
    """
    def __init__(self, matplotlibwidget: MatplotlibWidget, **kwargs):
        """
            For a given MatplotlibWidget, transparency picking can be enabled for legends
            and hiding legends, left, and right with the "H", "L", and "R" hotkeys respectively. 
            :param matplotlibwidget: The MatplotlibWidget for the given reading datatype.
            :type matplotlibwidget: MatplotlibWidget
        """
        self.fig = matplotlibwidget.canvas.figure
        self.mapLegendToAx = bidict()
        self.hideableLegends = []
        self.leftToHide = []
        self.rightToHide = []
        self.fig.canvas.mpl_connect('pick_event', self.on_pick)
        self.fig.canvas.mpl_connect('key_press_event', self.on_press)

    def addKneeAnglePlot(self, kneeAngleAxes: Axes) -> tuple[Line2D, Line2D]:
        """
            Adds an easy set of knee angle plots for the graph, returning a tuple of the lines for left and right.
        
            :param kneeAngleAxes: The plots that should have the leg lines added.
            :type kneeAngleAxes: Axes
            :return: Tuple of lines for the left and right legs.
            :rtype: tuple[Line2D, Line2D]
        """
        lineKneeAngleL, = kneeAngleAxes.plot([], [], label = "Left",  animated = False)
        lineKneeAngleR, = kneeAngleAxes.plot([], [], label = "Right",  animated = False)
        kneeAngleAxes.set_ylabel("$\\theta$ (deg)")
        kneeAngleAxes.grid(True)
        return lineKneeAngleL, lineKneeAngleR
    
    def addWindowedAngularVelocityPlot(self, windowedAngularVelocityAxes: Axes) -> tuple[Line2D, Line2D]:
        """
            Adds an easy set of windowed angular velocity plots for the graph, returning a tuple of the lines for left and right.
        
            :param windowedAngularVelocityAxes: The plots that should have the leg lines added.
            :type windowedAngularVelocityAxes: Axes
            :return: Tuple of lines for the left and right legs.
            :rtype: tuple[Line2D, Line2D]
        """
        lineWindowedAngularVelocityL, = windowedAngularVelocityAxes.plot([], [], label = "Left",  animated = False)
        lineWindowedAngularVelocityR, = windowedAngularVelocityAxes.plot([], [], label = "Right",  animated = False)
        windowedAngularVelocityAxes.set_ylabel("$\\dot{\\theta}$ (deg/s)")
        windowedAngularVelocityAxes.grid(True)
        return lineWindowedAngularVelocityL, lineWindowedAngularVelocityR

    def addFsrPlot(self, fsrAxes: Axes) -> tuple[Line2D, Line2D]:
        """
            Adds an easy set of FSR plots for the graph, returning a tuple of the lines for left and right.
        
            :param fsrAxes: The plots that should have the leg lines added.
            :type fsrAxes: Axes
            :return: Tuple of lines for the left and right legs.
            :rtype: tuple[Line2D, Line2D]
        """
        lineFsrL, = fsrAxes.plot([], [], label = "Left",  animated = False)
        lineFsrR, = fsrAxes.plot([], [], label = "Right",  animated = False)
        fsrAxes.set_ylabel("FSR (mV)")
        fsrAxes.grid(True)
        return lineFsrL, lineFsrR
    
    def addTorquePlot(self, torqueAxes: Axes) -> tuple[Line2D, Line2D]:
        """
            Adds an easy set of torque plots for the graph, returning a tuple of the lines for left and right.
        
            :param torqueAxes: The plots that should have the leg lines added.
            :type torqueAxes: Axes
            :return: Tuple of lines for the left and right legs.
            :rtype: tuple[Line2D, Line2D]
        """
        lineDesiredRestrictionsL, = torqueAxes.plot([], [], label = "Desired with Restrictions Left", animated = False)
        lineDesiredRestrictionsR, = torqueAxes.plot([], [], label = "Desired with Restrictions Right", animated = False)
        torqueAxes.set_ylabel("$\\tau$ (Nm)")
        torqueAxes.grid(True)
        return lineDesiredRestrictionsL, lineDesiredRestrictionsR
    
    def getFigure(self) -> Figure:
        """
            Gets the Matplotlib figure of the graph.

            :return: The Figure of the plots.
            :rtype: matplotlib.Figure 
        """
        return self.fig
    
    def getAxes(self) -> Axes:
        """
            Gets the Matplotlib axes of the graph.

            :return: The Axes of the plots.
            :rtype: matplotlib.Axes 
        """
        return self.axes
    
    def getAxesMaps(self) -> dict[type, dict[str, Line2D]]:
        """
            Gets the hierarchical structure of the graph lines by NamedTuple type, then by attribute name.

            :return: Line2D oriented by NamedTuple type attributes
            :rtype: dict[type, dict[str, Line2D]]
        """
        return self.axisMaps
    
    def getFigureAxesAxesMapTriple(self) -> tuple[Figure, Axes, dict[type, dict[str, Line2D]]]:
        """
            Returns the triple of the three components of Figure, Axes, and mapping of Line2Ds.

            :return: The triple of components.
            :rtype: tuple[Figure, Axes, dict[type, dict[str, Line2D]]]
        """
        return self.fig, self.axes, self.axisMaps
    
    def addOnPickEvent(self, legend: Legend, linesByLabel: dict[str, Line2D]) -> None:
        """
            Adds in the event for each of the lines by the label, setting in how 
            far to click before it is selected.

            :param legend: The legend item that references the line object.
            :type legend: Legend
            :param linesByLabel: A dictionary of labels and the lines that connects the line to legend.
            :type linesByLabel: dict[str, Line2D]
            :return: None
            :rtype: None

        """
        pickradius = 5  # How close the click needs to be to trigger an event.

        if legend is not None:
            for legendLine, axLine in zip(legend.get_lines(), linesByLabel.values()):
                legendLine.set_picker(pickradius)
                self.mapLegendToAx[legendLine] = axLine

    def setHideableLegends(self, legends: list[Legend]) -> None:
        """
            Sets in the legends that are hideable with "H".
        
            :param legends: List of legends that should be hideable with "H".
            :type legends: list[Legend]
            :return: None
            :rtype: None
        """
        self.hideableLegends.extend(legends)
    
    def setHideableLines(self, leftLines: list[Line2D], rightLines: list[Line2D]) -> None:
        """
            Sets in the lines for left and right that are hideable with "L" and "R" respectively.
            :param leftLines: Left lines to be hidden with "L".
            :type leftLines: list[Line2D]
            :param rightLines: Right lines to be hidden with "R".
            :type rightLines: list[Line2D]
            :return: None
            :rtype: None
        """
        self.leftToHide.extend(leftLines)
        self.rightToHide.extend(rightLines)

    def addPickableLegend(self, axes: Axes, lines: list[Line2D], numCols: int = None, fontsize: str = 'medium') -> tuple[Legend, dict[str, Line2D]]:
        """
            Adds a legend where the lines are pickable given a set of lines.

            :param axes: The Axes objects where the legend should be.
            :type axes: Axes
            :param lines: The list of lines that should be on the legend.
            :type lines: list[Line2D]
            :param numCols: The number of columns in the legend.
            :type numCols: int
            :param fontsize: The size of the font in the legend.
            :type fontsize: str

            :return: A tuple of the Legend and lines labeled by name.
            :rtype: tuple[Legend, dict[str, Line2D]]
        """
        cols = numCols if numCols is not None else round(len(lines) / 2)
        legend, linesByLabel = None, None
        if len(lines) != 0:
            linesByLabel = {l.get_label(): l for l in lines} # get_label() just returns a string
            legend = axes.legend(linesByLabel.values(), linesByLabel.keys(),   
                        loc = 'upper right', ncol = cols, fontsize = fontsize)
            legend.set_draggable(True)
        return legend, linesByLabel
    
    def addThresholdLines(axes: Axes, colors: list[str], labels: list[str], thresholdNames: list[str], isLeft: bool, **kwargs) -> list[Line2D]:
        """
            Add threshold lines to the plot. Left is considered dash line, while right is considered solid line.
            
            :param axes: The axes (plot) to add the lines.
            :type axes: Axes
            :param colors: list of colors that are zipped with the threshold names.
            :type colors: list[str]
            :param labels: list of string labels that are zipped with the threshold names.
            :type labels: list[str]
            :param thresholdNames: list of threshold names to be used (left and right are automatically appended)
            :type thresholdNames: list[str]
            :param isLeft: Whether or not the threshold line is left or right.
            :type isLeft: bool

            :return: List of threshold line objects that were added.
            :rtype: list[Line2D]
        """
        updatedLabels = []
        for label in labels:
            updatedLabels.append(f"{label} (L)" if isLeft else f"{label} (R)")
        linestyle = 'dashed' if isLeft else 'solid'

        horizontalLines = []
        for thresholdName, color, updatedLabel in zip(thresholdNames, colors, updatedLabels):
            thresholdValue = kwargs.get(thresholdName)
            if thresholdValue is not None:
                horizontalLine = axes.axhline(y = thresholdValue, color = color, linestyle = linestyle, label = f"{updatedLabel} — {thresholdValue}")
                horizontalLines.append(horizontalLine)
        return horizontalLines

    def on_press(self, event) -> None:
        """
            Callback function to handle hotkey changes. Namely "H" toggles legend visibility,
            "L" toggles left, and "R" toggles right leg visibilities.
        """
        if event.key == 'h':
            for legend in self.hideableLegends:
                legend.set_visible(not legend.get_visible())
        elif event.key == 'l' or event.key == 'r':
            legToHide = self.leftToHide if event.key == 'l' else self.rightToHide
            if legToHide:
                for line in legToHide:
                    if line not in self.mapLegendToAx.inv: # Guarantees that we find a non-legend element.
                        break

                visible = not line.get_visible()
                for legLines in legToHide:
                    legLines.set_visible(visible)
                    
                    # Update any of the legends for visibility
                    if legLines in self.mapLegendToAx.inv:
                        legendLine = self.mapLegendToAx.inv[legLines]
                        legendLine.set_alpha(1.0 if visible else 0.2)
        self.fig.canvas.draw()

    # Legend picking from https://matplotlib.org/stable/gallery/event_handling/legend_picking.html
    def on_pick(self, event):
        """
            Callback function to handle legend picking. Handles toggling visibility of the lines
            if selected from the legend. More fine-grained than the hotkeys.
        """
        # When using this, mapLegendToAx must be set.

        # On the pick event, find the original line corresponding to the legend
        # proxy line, and toggle its visibility.
        legendLine = event.artist

        # Do nothing if the source of the event is not a legend line.
        if legendLine not in self.mapLegendToAx:
            return

        axLine = self.mapLegendToAx[legendLine]
        visible = not axLine.get_visible()
        axLine.set_visible(visible)
        # Change the alpha on the line in the legend, so we can see what lines
        # have been toggled.
        legendLine.set_alpha(1.0 if visible else 0.2)
        self.fig.canvas.draw()

    @staticmethod
    def removeTickNumbers(axes: np.ndarray) -> None:
        """
            Removes all of the tick numbers on all of the axes except for the last one.

            :param axes: Axes containing the plots.
            :type axes: Axes
            :return: None
            :rtype: None
        """
        rows, cols = axes.shape
        # Everything except the last row, remove the tick numbers.
        for row in range(0, rows - 1):
            for col in range(0, cols):
                axes[row, col].tick_params(axis = 'x', which = 'both', labelsize = 0)
        
        # All the last rows, add the label.
        for col in range(0, cols):
            axes[rows - 1, col].set_xlabel("t (s)")

    @abstractmethod
    def updateFinalPlotMatplotlib(self, **kwargs) -> None:
        """
            Method that can be used to update the plots at the final moment
            after autoscaling for fitting the plots has been used. May be used
            to override any changes.

            :params kwargs: Keyword arguments that may be used in final fitting of plots.
            :types dict[str, Any]
            :return: None
            :rtype: None
        """
        pass

#    The rest of these functions are specific for pyqtgraph layouts and graphing.
def setGraphLayout(graphicsLayoutWidget: GraphicsLayoutWidget) -> None:
    """
        Sets the GraphicLayoutWidget to minimal margins and little spacing.

        :params graphicsLayoutWidget: The GraphicsLayoutWidget to change.
        :type graphicsLayoutWidget: GraphicsLayoutWidget
        :return: None
        :rtype: None
    """
    graphicsLayoutWidget.centralWidget.layout.setContentsMargins(0, 0, 0, 0)
    graphicsLayoutWidget.centralWidget.layout.setSpacing(10)

def setPlotLayout(plots: np.ndarray) -> None:
    """
        Set the graphs to be equally sized with each other.

        :params plots: Set of PlotItems that should have their size set.
        :type plots: numpy.ndarray[PlotItems]
        :return: None
        :rtype: None
    """
    graphSizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Ignored)
    graphSizePolicy.setHorizontalStretch(0)
    graphSizePolicy.setVerticalStretch(0)

    # Set so that graphs are equally sized.
    for plot in plots.flat:
        plot.setSizePolicy(graphSizePolicy)

def getLeftLabelFontFormat(ptSize: int = 12) -> QtGui.QFont:
    """
        Creates the font format for the left axis of each graph.
        :param ptSize: The size of the font.
        :type ptSize: int
        :return: The font to use in the graphs.
        :rtype: QtGui.QFont
    """
    axisLabelFont = QtGui.QFont()
    axisLabelFont.setPointSize(ptSize)
    axisLabelFont.setStyleStrategy(QtGui.QFont.StyleStrategy.PreferAntialias)
    return axisLabelFont

def addThresholdLines(plot: PlotItem, defaultThresholdValues: list[float], colors: list[str], 
                      leftThresholdNames: list[str], rightThresholdNames: list[str], lineFontSize: int = LINE_WIDTH) -> list[PlotDataItem]:
    """
        Adds threshold lines for the plots in pyqtgraph.

        :param plot: the plot to add the threshold lines into.
        :type plot: PlotItem
        :param defaultThresholdValues: The default threshold values that should be initially set.
        :type defaultThresholdValues: list[float]
        :param colors: The colors that should be used for the lines.
        :type colors: list[str]
        :param leftThresholdNames: List of names to be used on the left side.
        :type leftThresholdNames: list[str]
        :param rightThresholdNames:  List of names to be used on the right side.
        :type rightThresholdNames: list[str]
        :param lineFontSize: The side of the threshold line.
        :type lineFontSize: int

        :return: list of threshold lines that were added.
        :rtype: list[PlotDataItem]
    """
    thresholdLines = []
    for value, color, thresholdName in zip(defaultThresholdValues, colors * 2, leftThresholdNames + rightThresholdNames):
        style =  QtCore.Qt.PenStyle.DotLine if thresholdName in leftThresholdNames else QtCore.Qt.PenStyle.SolidLine 
        thresholdLines.append(plot.addLine(y = value, pen = mkPen(color, width = lineFontSize, style = style),
                                            name = thresholdName))
    return thresholdLines

def addThresholdLegend(plot: PlotItem, thresholdLines: list[PlotDataItem]) -> LegendItem:
    """
        Adds a legend to the plot using the threshold lines as items.

        :param plot: the plot to add the threshold lines into.
        :type plot: PlotItem
        :param thresholdLines: List of threshold lines.
        :type thresholdLines: list[PlotDataItem]
        :return: Legend that contains the threshold lines
        :rtype: LegendItem
    """
    legend = plot.addLegend(offset = (-1, 1), brush = mkBrush(color = mkColor(255, 255, 255, 32)), colCount = len(thresholdLines) // 2)
    for thresholdLine in thresholdLines:
        thresholdLine.opts = {"pen": thresholdLine.pen} # Workaround for infinite line not having opts dictionary.
        legend.addItem(thresholdLine, thresholdLine._name) # Add to legend.
    return legend

def addLegLegend(plot: PlotItem, leftLeg: PlotDataItem, rightLeg: PlotDataItem) -> LegendItem: # Legend for blue/orange to distinguish which leg is which.
    """
        Adds the legend that contains the left and right legs as items.

        :param plot: The plot to add the threshold lines into.
        :type plot: PlotItem
        :param leftLeg: The line that corresponds to the left leg (often the knee angle line).
        :type leftLeg: PlotDataItem
        :param rightLeg: The line that corresponds to the right leg (often the knee angle line).
        :type rightLeg: PlotDataItem
        :return: The legend containing the left and right legs.
        :rtype: LegendItem
    """
    legend = plot.addLegend(offset = (-1, 1), brush = mkBrush(color = mkColor(255, 255, 255, 32)), colCount = 2)
    legend.addItem(leftLeg, "L")
    legend.addItem(rightLeg, "R")
    return legend

""" The four plots below are stock standard plots used for the sensor (and derived) data. Assumption made for these plots:
    - Knee Angle plot is available and thus will scroll with that plot.
    - Legends for thresholding are handled outside of these plots.
"""
def addKneeAnglePlot(fig: PlotItem, row: int, xGraphLim: int, axisLabelFont: QtGui.QFont, lineFontSize: int = 2) -> tuple[PlotItem, PlotDataItem, PlotDataItem]:
    """
        Adds a basic knee angle plot onto the plots. Plots are arranged in a single column, but placement
        of the plot can be changed with the row parameter.

        :param fig: The plot that should have the knee angle plot added.
        :type fig: PlotItem
        :param row: The row that this plot should be added onto.
        :type row: int
        :param xGraphLim: The maximum limits at which x-axis should be initially set for this plot.
        :type xGraphLim: int
        :param axisLabelFont: The font that should be used on the left side of the plot.
        :type axisLabelFont: QtGui.QFont
        :param lineFontSize: The size of the line for this plot. Default: 2.
        :type lineFontSize: int
        :return: Tuple of the plots, line for the left leg, and line for the right leg.
        :rtype: tuple[PlotItem, PlotDataItem, PlotDataItem]
    """
    # Basic Knee Angle Plot - for consistency, it's mostly assumed that it is the first plot (hence, (0,0) indexing).
    kneeAnglePlot = fig.addPlot(row = row, col = 0, name = "Knee Angle Plot", labels = {'left': "θ (deg)", 'bottom': "t (s)" })
    lineKneeAngleL = kneeAnglePlot.plot([], [], pen = mkPen(LEFT_COLOR, width = lineFontSize), name = "kneeAngleLeft", autodownsample = True, 
                                        downsampleMethod = 'subsample', clipToView = True, skipFiniteCheck = True)
    lineKneeAngleR = kneeAnglePlot.plot([], [], pen = mkPen(RIGHT_COLOR, width = lineFontSize), name = "kneeAngleRight", autodownsample = True, 
                                        downsampleMethod = 'subsample', clipToView = True, skipFiniteCheck = True)
    kneeAngleGrid = GridItem()
    kneeAngleGrid.setTickSpacing(x = [None, None], y = [-1.0, 15]) # Adding a negative value seems to remove the text labels.
    kneeAnglePlot.addItem(kneeAngleGrid)
    kneeAnglePlot.setRange(xRange = (-xGraphLim, 0), yRange = (-10, 80), padding = 0.05)
    kneeAnglePlot.getAxis('left').label.setFont(axisLabelFont)
    return kneeAnglePlot, lineKneeAngleL, lineKneeAngleR

def addSimKneeAngleLines(fig: PlotItem, lineFontSize: int = 0) -> tuple[PlotDataItem, PlotDataItem]:
    """
        Adds the simulator lines for the plot into the knee angle. These are not really used (inputs are not duplicated), 
        but are a reference point for setting lines together.

        :param fig: The plot where the knee angle lines are to be added.
        :type fig: PlotItem
        :param lineFontSize: Size of the line font. Default: 0.
        :type lineFontSize: int.
        :return: Tuple of the simulator lines.
        :rtype: tuple[PlotDataItem, PlotDataItem]
    """
    lineSimKneeAngleL = fig.plot([], [], pen = mkPen(LEFT_COLOR, width = lineFontSize, style = Qt.PenStyle.DotLine), name = "L-SIM", autodownsample = True, 
                                        downsampleMethod = 'subsample', clipToView = True, skipFiniteCheck = True)
    lineSimKneeAngleR = fig.plot([], [], pen = mkPen(RIGHT_COLOR, width = lineFontSize, style = Qt.PenStyle.DotLine), name = "R-SIM", autodownsample = True, 
                                        downsampleMethod = 'subsample', clipToView = True, skipFiniteCheck = True)
    return lineSimKneeAngleL, lineSimKneeAngleR

def addWindowedAngularVelocityPlot(fig: PlotItem, row: int, axisLabelFont: QtGui.QFont, lineFontSize: int = 2) -> tuple[PlotItem, PlotDataItem, PlotDataItem]:
    """
        Adds a basic windowed angular velocity plot onto the plots. Plots are arranged in a single column, but placement
        of the plot can be changed with the row parameter.

        :param fig: The plot that should have the windowed angular velocity plot added.
        :type fig: PlotItem
        :param row: The row that this plot should be added onto.
        :type row: int
        :param xGraphLim: The maximum limits at which x-axis should be initially set for this plot.
        :type xGraphLim: int
        :param axisLabelFont: The font that should be used on the left side of the plot.
        :type axisLabelFont: QtGui.QFont
        :param lineFontSize: The size of the line for this plot. Default: 2.
        :type lineFontSize: int
        :return: Tuple of the plots, line for the left leg, and line for the right leg.
        :rtype: tuple[PlotItem, PlotDataItem, PlotDataItem]
    """
    windowedAngularVelocityPlot = fig.addPlot(row = row, col = 0, name = "Windowed Angular Velocity Plot", labels = {'left': "θ' (deg/s)", 'bottom': "t (s)" })
    lineWindowedAngularVelocityL = windowedAngularVelocityPlot.plot([], [], pen = mkPen(LEFT_COLOR, width = lineFontSize), 
                                                                    name = "windowedAngularVelocityLeft", autodownsample = True, 
                                                                    downsampleMethod = 'subsample', clipToView = True, skipFiniteCheck = True)
    lineWindowedAngularVelocityR = windowedAngularVelocityPlot.plot([], [], pen = mkPen(RIGHT_COLOR, width = lineFontSize), 
                                                                    name = "windowedAngularVelocityRight", autodownsample = True, 
                                                                    downsampleMethod = 'subsample', clipToView = True, skipFiniteCheck = True)

    windowedAngularVelocityPlot.setRange(yRange = (-200, 200), padding = 0.00)
    windowedAngularVelocityPlot.setXLink("Knee Angle Plot") # Moving the X scale also moves the Knee Angle Plot scale and whatever also is linked to it.
    windowedAngularVelocityGrid = GridItem()
    windowedAngularVelocityGrid.setTickSpacing(x = [None, None], y = [-1.0, 50.0])
    windowedAngularVelocityPlot.addItem(windowedAngularVelocityGrid)
    windowedAngularVelocityPlot.getAxis('left').label.setFont(axisLabelFont)
    return windowedAngularVelocityPlot, lineWindowedAngularVelocityL, lineWindowedAngularVelocityR

def addFsrPlot(fig: PlotItem, row: int, axisLabelFont: QtGui.QFont, lineFontSize: int = 2) -> tuple[PlotItem, PlotDataItem, PlotDataItem]:
    """
        Adds a basic FSR plot onto the plots. Plots are arranged in a single column, but placement
        of the plot can be changed with the row parameter.

        :param fig: The plot that should have the FSR plot added.
        :type fig: PlotItem
        :param row: The row that this plot should be added onto.
        :type row: int
        :param xGraphLim: The maximum limits at which x-axis should be initially set for this plot.
        :type xGraphLim: int
        :param axisLabelFont: The font that should be used on the left side of the plot.
        :type axisLabelFont: QtGui.QFont
        :param lineFontSize: The size of the line for this plot. Default: 2.
        :type lineFontSize: int
        :return: Tuple of the plots, line for the left leg, and line for the right leg.
        :rtype: tuple[PlotItem, PlotDataItem, PlotDataItem]
    """
    fsrPlot = fig.addPlot(row = row, col = 0, name = "FSR Plot", labels = {'left': "FSR (mV)", 'bottom': "t (s)"})
    lineFsrL = fsrPlot.plot([], [], pen = mkPen(LEFT_COLOR, width = lineFontSize), name = "fsrLeft", autodownsample = True, 
                            downsampleMethod = 'subsample', clipToView = True, skipFiniteCheck = True)
    lineFsrR = fsrPlot.plot([], [], pen = mkPen(RIGHT_COLOR, width = lineFontSize), name = "fsrRight", autodownsample = True, 
                            downsampleMethod = 'subsample', clipToView = True, skipFiniteCheck = True)

    # Grid spacing of 200 mV
    fsrGrid = GridItem()
    fsrGrid.setTickSpacing(x = [None, None], y = [-1.0, 200.0])
    fsrPlot.addItem(fsrGrid)
    fsrPlot.setRange(yRange = (0, 9500), padding = 0.00)
    fsrPlot.setXLink("Knee Angle Plot")
    fsrPlot.getAxis('left').label.setFont(axisLabelFont)
    return fsrPlot, lineFsrL, lineFsrR

def addTorquePlot(fig: PlotItem, row: int, axisLabelFont: QtGui.QFont, lineFontSize: int = 2) -> tuple[PlotItem, PlotDataItem, PlotDataItem]:
    """
        Adds a basic torque plot onto the plots. Plots are arranged in a single column, but placement
        of the plot can be changed with the row parameter.

        :param fig: The plot that should have the torque plot added.
        :type fig: PlotItem
        :param row: The row that this plot should be added onto.
        :type row: int
        :param xGraphLim: The maximum limits at which x-axis should be initially set for this plot.
        :type xGraphLim: int
        :param axisLabelFont: The font that should be used on the left side of the plot.
        :type axisLabelFont: QtGui.QFont
        :param lineFontSize: The size of the line for this plot. Default: 2.
        :type lineFontSize: int
        :return: Tuple of the plots, line for the left leg, and line for the right leg.
        :rtype: tuple[PlotItem, PlotDataItem, PlotDataItem]
    """
    torquePlot = fig.addPlot(row = row, col = 0, name = "Torque Plot", labels = {'left': "τ (Nm)", 'bottom': "t (s)" })
    lineDesiredRestrictionsL = torquePlot.plot([], [], pen = mkPen(LEFT_COLOR, width = lineFontSize), 
                                            name = "Desired with Restrictions Left", autodownsample = True, downsampleMethod = 'subsample', 
                                            clipToView = True, skipFiniteCheck = True)
    lineDesiredRestrictionsR = torquePlot.plot([], [], pen = mkPen(RIGHT_COLOR, width = lineFontSize), 
                                            name = "Desired with Restrictions Right", autodownsample = True, downsampleMethod = 'subsample', 
                                            clipToView = True, skipFiniteCheck = True)
    torqueGrid = GridItem()
    torqueGrid.setTickSpacing(x = [None, None], y = [-1.0, 5.0])
    torquePlot.addItem(torqueGrid)
    torquePlot.setRange(yRange = (-10, 10), padding = 0.05)
    torquePlot.setXLink("Knee Angle Plot") # Moving the X scale also moves the Knee Angle Plot scale and whatever also is linked to it
    torquePlot.getAxis('left').label.setFont(axisLabelFont)
    return torquePlot, lineDesiredRestrictionsL, lineDesiredRestrictionsR

def addSimTorqueLines(fig: PlotItem, lineFontSize: int = 1) -> tuple[PlotDataItem, PlotDataItem]:
    """
        Adds the simulator torque lines for the torque plots. The simulator will use Dotted lines
        over the normal solid lines.

        :param fig: The plot that should have the simulator lines attached.
        :type fig: PlotItem
        :param lineFontSize: The font size that should be used in the lines. Default: 1.
        :type lineFontSize: int
        :return: Tuple of two lines representing the left and right simulator lines.
        :rtype: tuple[PlotDataItem, PlotDataItem]
    """
    lineSimDesiredRestrictionsL = fig.plot([], [], pen = mkPen(LEFT_COLOR, width = lineFontSize, style = Qt.PenStyle.DotLine), 
                                            name = "Sim Desired with Restrictions Left", autodownsample = True, downsampleMethod = 'subsample', 
                                            clipToView = True, skipFiniteCheck = True)
    lineSimDesiredRestrictionsR = fig.plot([], [], pen = mkPen(RIGHT_COLOR, width = lineFontSize, style = Qt.PenStyle.DotLine), 
                                            name = "Sim Desired with Restrictions Right", autodownsample = True, downsampleMethod = 'subsample', 
                                            clipToView = True, skipFiniteCheck = True)
    return lineSimDesiredRestrictionsL, lineSimDesiredRestrictionsR

""" For custom gap sizes use Qt.PenStyle.CustomDashLine
    then use setDashPattern(dot, gap)
"""

def addSimStateLines(fig: PlotItem, lineFontSize: int = 1) -> tuple[PlotDataItem, PlotDataItem]:
    """
        Adds the simulator state lines for the state plots. The simulator will use Dotted lines
        over the normal solid lines.

        :param fig: The plot that should have the simulator lines attached.
        :type fig: PlotItem
        :param lineFontSize: The font size that should be used in the lines. Default: 1.
        :type lineFontSize: int
        :return: Tuple of two lines representing the left and right simulator lines.
        :rtype: tuple[PlotDataItem, PlotDataItem]
    """
    lineSimStateL = fig.plot([], [], pen = mkPen(LEFT_COLOR, width = lineFontSize, style = Qt.PenStyle.DotLine), 
                                            name = "simStateLeft", autodownsample = True, downsampleMethod = 'subsample', 
                                            clipToView = True, skipFiniteCheck = True)
    lineSimStateR = fig.plot([], [], pen = mkPen(RIGHT_COLOR, width = lineFontSize, style = Qt.PenStyle.DotLine), 
                                            name = "simStateRight", autodownsample = True, downsampleMethod = 'subsample', 
                                            clipToView = True, skipFiniteCheck = True)
    return lineSimStateL, lineSimStateR

def updateLegend(legend: LegendItem) -> None:
    """ 
        Toggles the visibility of the legend. Used when pressing the "H" hotkey
        :params legend: The legend to change visibility.
        :type legend: LegendItem
        :return: None
        :rtype: None
    """
    legend.setVisible(not legend.isVisible())
    legend.setVisible(not legend.isVisible())