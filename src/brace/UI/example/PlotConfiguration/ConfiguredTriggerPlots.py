from matplotlib.axes import Axes
from matplotlib.lines import Line2D
from pyqtgraph.widgets.MatplotlibWidget import MatplotlibWidget

from brace.UI.PlotConfiguration.ConfigurePlotHelpers import MplBasePlot
from brace.Server.GPIOSynch.PushButton import Trigger

class TriggerPlotsMpl(MplBasePlot):
    """
        These are plots for displaying the synchronization trigger. There is no equivalent for the simulator or main GUI.
        This is only used for opening the data and determining the time at which the trigger was held high.
    """

    def __init__(self, matplotlibwidget: MatplotlibWidget, **kwargs):
        """
            Initializes the plots for only the trigger.

            :params matplotlibwidget: The widget that should contain the graphs.
            :type MatplotlibWidget: HideableElementsGraphicsLayoutWidget
            :params kwargs: Extra key-value parameters that may be used in initialization such as thresholds.
            :type kwargs: dict[str, Any]

            :return: None
            :rtype: None
        """
        super().__init__(matplotlibwidget, **kwargs)
        self.axes = self.fig.subplots(1, 1, squeeze = False, sharex=True)
        self.fig.subplots_adjust(hspace = 0.10, top = 0.99, bottom = 0.075, left = 0.075, right = 0.995)
        MplBasePlot.removeTickNumbers(self.axes)

        # Trigger Plot
        triggerAxes: Axes = self.axes[0, 0]
        lineTriggered, = triggerAxes.plot([], [], label = "Pin 24")
        triggerAxes.set_xlabel("t (s)")
        triggerAxes.set_ylabel("Time Sync")
        triggerAxes.grid(True)

        triggerAxisLines: dict[str, Line2D] = { 'triggerState' : lineTriggered }
        self.axisMaps = { Trigger: triggerAxisLines }

    def updateFinalPlotMatplotlib(self, **kwargs) -> None:
        triggerAxes: Axes = self.axes[0, 0]
        triggerAxes.set_ylim(bottom = 0, top = 1.5)