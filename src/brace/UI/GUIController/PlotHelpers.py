from __future__ import annotations
from functools import partial
from PySide6.QtCore import Slot, Qt
from PySide6.QtGui import QPalette, QActionGroup
from matplotlib.axes import Axes
from pyqtgraph import GraphicsLayoutWidget, mkBrush, mkColor, PlotItem, mkPen
from PySide6.QtWidgets import QCheckBox, QMainWindow
from typing import TYPE_CHECKING
import numpy as np

from brace.UI.GraphContext import GraphContext

if TYPE_CHECKING:
    from brace.UI.example.MainWindow import MainWindow

import logging
logger = logging.getLogger("logger")

@Slot(QMainWindow) # But also a regular function
def changePlotBackground(parent: MainWindow) -> None:
    """
        Goes through the GraphContexts of the MainWindow
        changing all the plots to have a dark background color if dark mode
        is used, and white background is light mode is used.

        :param parent: The MainWindow containing the GraphContexts.
        :type parent: MainWindow
        :return: None
        :rtype: None
    """

    # A quick and dirty way to check for light/dark independent of OS platform to work around Linux. 
    # Note that the last value (alpha) is always 255.
    rgb = parent.app.palette().color(QPalette.ColorRole.Window).getRgb()
    isLight = all(rgbValue >= 128 for rgbValue in rgb[0:2])

    for graphContext in parent.graphContexts:
        widget = graphContext.fig
        axes = graphContext.axes
        if isinstance(widget, GraphicsLayoutWidget):
            # Default is dark.
            if (parent.actionSystemDefault.isChecked() and isLight) or parent.actionLightMode.isChecked():
                backgroundColor = 'w'
                foregroundColor = 'k'
            else:
                backgroundColor = 'k'
                foregroundColor = 'w'

            widget.setBackground(mkBrush(color = mkColor(backgroundColor)))
            ax: PlotItem
            for ax in axes.flat:
                for axisDirection in ['left', 'right', 'bottom', 'top']:
                    axis = ax.getAxis(axisDirection)
                    axis.setPen(mkPen(color = mkColor(foregroundColor)))
                    axis.setTextPen(mkPen(color = mkColor(foregroundColor)))

def createHidingBoxes(parent: MainWindow, graphContexts: list[GraphContext]) -> None:
    """
        Populate the checkboxes that hide the plots when not needed. This is done
        across all of the GraphContexts.

        :param parent: The parent object calling this method, containing the GraphContexts
        that should have their plots with hiding checkboxes.
        :type parent: MainWindow
        :param graphContext: GraphContexts containing the plots with that should have their plots with hideable checkboxes.
        :type graphContext: list[GraphContext]

        :return: None
        :rtype: None
    """
    # Two scenarios exist where this crashes rather dramatically.
    # 1) Toggling visibility during drawing. More notably, when show() is done. hide() is usually okay. 
    #       - One way to deal with this is prevent toggling visibility while drawing.
    #       - This issue actually is a result from the Grid lines when they aren't supposed to be drawn. And someone beat me to the chase by 1 day.
    #           - Relevant pull request: https://github.com/pyqtgraph/pyqtgraph/pull/3284. So it'll probably be fixed by next release.
    # 2) If you decide to remove all of the plots, and then try to toggle them back up, all of the plots start drawing on the same place. Then it crashes.
    #       - One way to deal with this is to stop the user from being able to remove all of the plots in the first place (i.e. at least one plot has to be drawn). 
    #       - Another way of dealing with this is to hide the graph widget instead of the plots, and repopulate the needed plots on re-entry.
    #       - The crashing is a result from the 1).
    for graphContext in graphContexts:
        axes = graphContext.axes
        for row in range(len(axes)):
            for col in range(len(axes[row])):
                plot = axes[row][col]
                name = plot.getViewBox().name # Kind of dangerous way to handle getting the name of each plot (as this doesn't have any related API call to it)
                checkbox = QCheckBox(name, parent)
                checkbox.setChecked(True)
                checkbox.toggled.connect(partial(setPlotVisibility, graphContext, (row, col)))
                graphContext.toggleHBoxLayout.addWidget(checkbox)
        showBottomRowLabel(axes)

@Slot()
def setPlotVisibility(graphContext: GraphContext, plotIndexesToHide: tuple[int, int], shouldBeVisible: bool) -> None:
    """
        Sets the visibility of the plots should the checkbox be unchecked, hiding them as necessary.

        :param graphContext: The graphContext containing the plot that should be hidden or shown.
        :type graphContext: GraphContext
        :param plotIndexesToHide: The tuple indicies of the plot that should be hidden.
        :type plotIndexesToHide: tuple[int, int]
        :param shouldBeVisible: Whether or not the plots should be hidden or shown.
        :type shouldBeVisible: bool

        :return: None
        :rtype: None
    """
    axes = graphContext.axes
    plotToSetVisibility: PlotItem = axes[plotIndexesToHide]
    plotName = plotToSetVisibility.getViewBox().name

    # This works around issue in Pyqtgraph where if all graphs are hidden, then the viewing bounding box becomes corrupted
    # when graphs are reshown.
    if not graphContext.fig.isVisible() and shouldBeVisible:
        # When the widget comes out of hiding, plots need to be hidden except the one on the menu. Then the widget can be reshown.
        plotToSetVisibility.show()
        for plot in axes.flat:
            if plot is not plotToSetVisibility:
                plot.hide()
        showBottomRowLabel(axes)
        graphContext.fig.show()
    elif not shouldBeVisible and not canHide(axes, plotIndexesToHide): 
        # Hide the widget instead of the plot so that corruption doesn't happen, but nothing is displayed.
        graphContext.fig.hide()
    else:
        plotToSetVisibility.setVisible(shouldBeVisible)
        showBottomRowLabel(axes)
    logger.info(f"{plotName} is set to {"visible" if shouldBeVisible else "hidden"}.")

def showBottomRowLabel(axes: np.ndarray[PlotItem]) -> None:
    """
        Adjusts the plots so that only the last plot shows the axis bottoms (since all the plots)
        have linked X-axes. This changes when plots are hidden and shown.

        :param axes: The set of plots containing the last plot to show axis bottoms.
        :type axes: numpy.ndarray[PlotItem]
        
        :return: None
        :rtype: None
    """
    # There is a slight pause when showing the time label axis, but it's probably okay.
    def showBottomAxisLabels(plot: PlotItem, show: bool):
        plot.getAxis('bottom').setStyle(showValues = show)
        plot.getAxis('bottom').showLabel(show = show)

    # Look through each column for the last visible plot.
    transposedAxes = np.transpose(axes)
    for plotCols in transposedAxes:
        bottomReached = False
        for plot in reversed(plotCols): 
            if plot.isVisible():
                if not bottomReached:
                    showBottomAxisLabels(plot, True)
                    bottomReached = True
                else:
                    showBottomAxisLabels(plot, False)

def canHide(axes: np.ndarray[PlotItem], plotIndexToCheck: tuple[int, int]) -> None:
    """
        Helper function to determine whether it is the last plot (and thus shouldn't be hidden)
        to workaround issue with corrupted graphs on hiding.
        
        :param axes: The set of plots containing hideable plots.
        :type axes: numpy.ndarray[PlotItem]
        :param plotIndexToCheck: A tuple containing the indicies of the plot to check.
        :type plotIndexToCheck: tuple[int, int]

        :return: None
        :rtype: None
    """
    # Look through each column for the last visible plot.
    for plot in axes.flat:
        if plot.isVisible() and axes[plotIndexToCheck] is not plot:
            return True
    return False

def setColorActionGroups(parent: MainWindow) -> QActionGroup:
    """
        Sets up the ActionGroup in the menu panel to trigger changing the style
        when light/dark mode is changed.

        :param parent: The main GUI that is running this command.
        :type parent: MainWindow | Simulator

        :return: The QActionGroup that handles the style changes.
        :rtype: QActionGroup
    """
    # QT Designer does not have a great way to set ActionGroups
    # Sets up toggle between light and dark mode
    colorActionGroup = QActionGroup(parent)
    colorActionGroup.addAction(parent.actionLightMode)
    colorActionGroup.addAction(parent.actionDarkMode)
    colorActionGroup.addAction(parent.actionSystemDefault)
    colorActionGroup.setExclusive(True)
    colorActionGroup.triggered.connect(lambda _: changeStyle(parent))
    return colorActionGroup

@Slot()
def changeStyle(parent: MainWindow) -> None:
    """
        Changes the style by applying the stylehint color scheme for the Qt window.

        :param parent: The main GUI that is running this command.
        :type parent: MainWindow
    
        :return: None
        :rtype: None
    """
    if parent.actionSystemDefault.isChecked():
        colorMode = "System Default"
        colorToSet = Qt.ColorScheme.Unknown
    elif parent.actionLightMode.isChecked():
        colorMode = "Light Mode"
        colorToSet = Qt.ColorScheme.Light
    elif parent.actionDarkMode.isChecked():
        colorMode = "Dark Mode"
        colorToSet = Qt.ColorScheme.Dark
    
    parent.app.styleHints().setColorScheme(colorToSet)
    logger.info(f"Changed to {colorMode}.")