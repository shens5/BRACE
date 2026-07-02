from __future__ import annotations
import dill
import matplotlib.pyplot as plt
import time
from matplotlib.figure import Figure
from matplotlib.axes import Axes
from matplotlib.lines import Line2D
from matplotlib.animation import FuncAnimation
from matplotlib.artist import Artist
import numpy as np
from multiprocessing import Queue
from threading import Event
from typing import NamedTuple
from collections.abc import Callable
from enum import IntEnum
from .DataStream import DataStream
from pyqtgraph import GraphicsLayoutWidget, PlotItem, PlotDataItem
from functools import partial
from queue import Empty
import logging
logger = logging.getLogger("logger")

class MismatchedTupleException(Exception):
    """ Raised for differences between the size of the tuple from the producer and the total number of datasets in the graph being drawn. """

class RealTimeType(IntEnum):
    """ Enum for classifying two types of real time drawing. """
    WRAPAROUND = 0,
    SLIDING_WINDOW = 1

class FigureAxes():
    def _default_pass(fig: GraphicsLayoutWidget | Figure, ax: np.ndarray[Axes] | np.ndarray[PlotItem], **kwargs):
        pass

    def __init__(self, fig: GraphicsLayoutWidget | Figure, ax: np.ndarray[Axes] | np.ndarray[PlotItem], func: Callable[[Figure, np.ndarray[Axes], dict], None] = None):
        self.fig = fig
        self.ax = ax
        self.bg = None # Needed only for Matplotlib's background animation in blitting.
        self.func = func if func is not None else FigureAxes._default_pass
        self.animation = None

class AnimatedGraphManager():
    """ Class that manages a set of animated plots and stores in the data internally.
        This serves as a consumer of a queue that takes in a NamedTuple that 
        contains n number of measurements and a timestamp.
    """

    def __init__(self, TRIAL_TIME: float = 0, FPS: int = 20, realTimeType: RealTimeType = RealTimeType.WRAPAROUND,
                 backend: str = "matplotlib"):
        """ 
            :param TRIAL_TIME: Used in fixed length trial times, specifically for Matplotlib. Mostly deprecated for pyqtgraph.
            :type TRIAL_TIME: float
            :param FPS: The attempted frames per second that should be targeted for Matplotlib. Also mostly deprecated for pyqtgraph.
            :type FPS: int
            :param realTimeType: The type of real time graph that details what happens when it reaches the right side. 
                WRAPAROUND represents the graph reaching the end before wrapping around from the left.
                SLIDING_WINDOW represents the graph reaches the end and the view of the data moves forward in time.
            :type realTimeType: RealTimeType
            :param backend: Either "matplotlib" or "pyqtgraph". The types of the parameters should also correspond to which backend used.
            i.e. GraphicsLayoutWidget, list[PlotItem] for "pyqtgraph" and Figure and np.ndarray[Axes] for "matplotlib".
            :type backend: str
        """

        self.TRIAL_TIME = TRIAL_TIME
        self.DRAW_UPDATE_TIME = 1 / FPS
        self.datastreams: dict[str, DataStream] = {}
        self.figureAxes: dict[str, FigureAxes] = {}
        self.animations: list[FuncAnimation] = []

        self.realTimeType = realTimeType
        self.queue = Queue()
        self.backend = backend
        self.isStreaming = Event()

        self.performanceTimer = 0
        self.counter = 0
        self.previousTime = 0
        self.bg = None

    def addNewDatastream(self, fig: Figure | GraphicsLayoutWidget, ax: np.ndarray[Axes] | np.ndarray[PlotItem],
                         namedTupleType: type, propertyDataMapping: dict[str, Line2D] | dict[str, PlotDataItem], 
                         graphDownSampleRate: int = 20, MAX_TIME_RANGE: float = 10, func: Callable[[Figure, np.ndarray[Axes], dict], None] = None) -> None:
        """
            Registers a new NamedTuple type and the corresponding plots and lines to be graphed.

            :param fig: Preconfigured figure from plt.subplots(). Or the GraphicsLayoutWidget that is in the GUI.
            :type fig: matplotlib.figure.Figure | pyqtgraph.GraphicsLayoutWidget
            :param ax: Axes preconfigured from plt.subplots() or handcreated for pyqtgraph. 
                Most likely a 2D array used to manipulate the subplots.
            :type ax: numpy.ndarray[matplotlib.axes.Axes] | numpy.ndarray[PlotItem]
            :param namedTupleType: A NamedTuple implementation (type) that represents a datapoint for this particular datastream.
            :type namedTupleType: type
            :param propertyDataMapping: A dictionary mapping between the lines and the instance variables
                of the namedTupleType.
            :type propertyDataMapping: dict[str, Line2D] | dict[str, PlotDataItem]
            :param graphDownSampleRate: The number of samples in between a datapoint when real time graphing.
            :type graphDownSampleRate: int
            :param MAX_TIME_RANGE: The length of time in seconds that the graphing will sample (i.e. from the last datapoint, how far back it should start).
            :type MAX_TIME_RANGE: float
            :param func: Callback function that handles the final drawing of the graph after finishing the real time graph.
            :type func: Callable[[Figure, np.ndarray[Axes], dict], None]
            :return: None
            :rtype: None
        """
        associatedAxes: set[Axes] | set[PlotItem] = set() # Set of subplots who have at least one line in the Datastream

        if self.backend == 'matplotlib':
            axis: Axes
            datalines: Line2D
            for datalines in propertyDataMapping.values():
                if datalines:
                    associatedAxes.add(datalines.axes)
        elif self.backend == 'pyqtgraph':
            axis: PlotItem
            for datalines in propertyDataMapping.values():
                for axis in ax.flat:
                    axisLines = set(axis.listDataItems())

                    if datalines in axisLines:
                        associatedAxes.add(axis)
            
        associatedAxes = list(associatedAxes)
        self.datastreams[namedTupleType.__name__] = DataStream(fig, associatedAxes, propertyDataMapping, namedTupleType, 
                                                      graphDownSampleRate = graphDownSampleRate, MAX_TIME_RANGE = MAX_TIME_RANGE, backend = self.backend)
        self.figureAxes[namedTupleType.__name__] = FigureAxes(fig = fig, ax = ax, func = func)
    
    def getQueue(self) -> Queue:
        """
            Returns the multiprocessing queue that should be used for queuing NamedTuple messages.
            
            :return: Multiprocessing queue that the AnimatedGraphManager should use for
            reading datapoints.
            :rtype: multiprocessing.Queue
        """
        return self.queue
    
    def setQueue(self, queue: Queue) -> None:
        """
            Supplies a multiprocessing queue (other than the one created automatically in the AnimatedGraphManager)
            that should be used for reading datapoints in this AnimatedGraphManager.

            :param queue: The multiprocessing queue to read from.
            :return: None
            :rtype: None
        """
        self.queue = queue

    def setupAnimation(self, fig: Figure) -> None:
        """
            Sets up an matplotlib animation for the figure. Blitting is done to
            increase performance.

            :param fig: The matplotlib figure to be animated.
            :type fig: Figure
            :return: None
            :rtype: None
        """
        DRAW_UPDATE_TIME_MS = self.DRAW_UPDATE_TIME * 1000
        if self.backend == "matplotlib":
            self.animations.append(FuncAnimation(fig, func = partial(self._drawAnimation, fig = fig), interval = DRAW_UPDATE_TIME_MS, cache_frame_data = False, 
                                        blit = True, repeat = False))
    
    
    def clearQueues(self) -> None:
        """
            Empties the multiprocessing queue to remove old datapoints that may be in the queue
            to prevent leakages into future plots.

            :return: None
            :rtype: None
        """
        try: 
            while not self.queue.empty():
                try:
                    self.queue.get_nowait()
                except Empty:
                    pass # Explicitly mask the queue.Empty
        except ConnectionResetError:
            logger.error("AnimatedGraphManager Queue was forcibly closed by remote host.")
            
    # Close the queues
    def close(self) -> None:
        """
            Closes the queue for any processing. Commands other than setting
            the multiprocessing queue are not considered safe.

            :return: None
            :rtype: None
        """
        self.queue.close()

    def reset(self) -> None:
        """
            Resets the datalines in this AnimatedGraphManager for all data.
            Flags for streaming are also reset. This should be performed
            every stream session.

            :return: None
            :rtype: None
        """
        self.counter = 0
        for datastream in self.datastreams.values():
            datastream.clearData()
        self.isStreaming.clear()

    def getCounter(self) -> None:
        return self.counter

    def qtRun(self) -> None:
        """
            This function should be run in the background (thread-level parallelism) when data streaming
            is executed. This parses the datapoints, but does not draw them outright. For pyqtgraph plots.

            :return: None
            :rtype: None
        """
        while not self.isStreaming.is_set():
            nextFrameTime = time.monotonic() + 1/225
            self._parseDatapoints(maxPoints = 250)
            sleepTime = nextFrameTime - time.monotonic()
            if sleepTime > 0: # Sleep until the next frame
                time.sleep(sleepTime)
    
    def qtDraw(self, fig: GraphicsLayoutWidget) -> None:
        """
            This function should be executed periodically on a timer (QTimer works well) during data streaming.
            This plots the datapoints of the figure given; not all figures are drawn as an optimization.

            :param fig: The GraphicsLayoutWidget or Figure whose plots should be drawn using the currently available
                datapoints.
            :type fig: GraphicsLayoutWidget
            :return: None
            :rtype: None
        """
        if self.counter == 0:
            self.performanceTimer = time.perf_counter()

        self.counter += 1
        lines = self._drawAnimation(None, fig = fig)

        if self.backend == 'matplotlib':
            # TODO: Still need to update these so that each figure has an empty background
            if not self.bg:
                self.bg = fig.canvas.copy_from_bbox(fig.bbox)

            fig.canvas.restore_region(self.bg)
            for line in lines:
                line.axes.draw_artist(line)
            fig.canvas.blit(fig.bbox)
            fig.canvas.flush_events()

    def _parseDatapoints(self, maxPoints: int) -> None:
        # Parses the datapoints, filtering out messages that don't have registered
        # NamedTuples to them.
        collectedDatapoints = self._receiveDatapoints(queue = self.queue, maxPoints = maxPoints)
        if collectedDatapoints:
            filteredDatapoints = filter(lambda item: item[0].__name__ in self.datastreams, collectedDatapoints.items())
            for namedTupleType, nameTuplePoint in filteredDatapoints:
                mappedMergedDatapoints = self._mergeDataPointsToDataStream(nameTuplePoint)
                mergedTimeData = mappedMergedDatapoints.pop('t') # Remove 't' and merge it to the datastream
                self.datastreams[namedTupleType.__name__].updateTime(mergedTimeData)
                for property, mergedDatapoints in mappedMergedDatapoints.items():
                    self.datastreams[namedTupleType.__name__].updatePoints(property, mergedTimeData, mergedDatapoints)

    def noAnimation(self) -> None:
        """
            This function simply parses all of the data until all the data is empty.
            This is most useful in plotting static plots, such as those with the Simulator.

            :return: None
            :rtype: None
        """
        while not self.queue.empty():
            self._parseDatapoints(1000)

    def mplStart(self) -> None:
        """ Main loop that reads the queue and updates the plot, within a specific time frame. 
            This is a legacy plotting to be used with Matplotlib.
        
            :return: None
            :rtype: None
        """
        if self.backend == 'matplotlib':
            plt.show(block = False)

        # Dataset to (Figure, Axes) assumptions.
        # One Figure + Axes can have multiple Datastreams.
        # There can be multiple Figure + Axes (means multiple windows, or pages in GUI). Each having at least one Dataset.
        # One datastream cannot be passed around multiple Figure + Axes. 
        # Each Figure + Axes should be only drawn once per frame. There should only be one animation per Figure (thus one animation per datastream).
        # Axes is part of the figure. But there isn't a simple way to get this relationship from PyQtGraph.
        #   - Each animation to its figure should only have its datastreams drawn and not any other figure's datastreams.
        #       - Thus there needs to be some relationship between a single figure and its datastreams where it can reference which lines need to be updated.
        #       - Action: Assigning figures and collecting the datastreams via NamedTupleType. Then passing a list of these datastreams to __drawAnimation.  
        # Each Figure + Axes should be able to be attached a hook at the end of the Final Draw. But only once per Figure.
        #   - NamedTuple reference to Figure + Axes might still be best way, but know that it still has access to parts of the figure that don't apply. 
        #       - Conflicting changes will mean that whatever is last done stays. 
        # Multiple AnimatedGraphManagers is off the table because we still want multiple datastreams in a single file.
        uniqueFigures: set[Figure] = set()
        for figureAxes in self.figureAxes.values():
            uniqueFigures.add(figureAxes.fig)
        
        for fig in uniqueFigures:
            self.setupAnimation(fig)

        frameCount = 0
        drawStartTime = time.time() # time.time is okay, this timing doesn't need to be very precise, save that for the actual data processes.
        endTime = time.time()+ self.TRIAL_TIME
        figuresChanged: set[Figure] = set()

        while time.time() <= endTime or not self.queue.empty():
            nextFrameTime = time.time() + self.DRAW_UPDATE_TIME
            figuresChanged.clear()

            self._parseDatapoints(maxPoints = 1000)
            frameCount += 1

            if self.backend == 'matplotlib':
                for fig in figuresChanged:
                    fig.canvas.start_event_loop(0.0001) # unlike plt.pause(0.0001), this doesn't force window focus.
            sleepTime = nextFrameTime - time.time()
            if sleepTime > 0: # Sleep until the next frame
                time.sleep(sleepTime)
        # print(f"FPS: {frameCount/(time.time() - drawStartTime)}")

        if self.backend == 'matplotlib':
            for animation in self.animations:
                animation.pause() # Stop the animation loop after ending.

    def _receiveDatapoints(self, queue: Queue, maxPoints: int = 15) -> dict[type, list[NamedTuple]]:
        """ 
            Polls the queue for namedtuples and collates them into a list, 
            until it reads that the queue is empty. Since the producer creates at a higher rate
            than the consumer, batching these datapoints together should be practical than one-to-one appending. 
            
            :params queue: Queue that is shared between the producer and the consumer (the AnimatedGraphManager).
            :type queue: multiprocessing.Queue
            :param maxPoints: The maximum number of points to read per data read.
            :type maxPoints: int
            :return: Dictionary of list of NamedTuples, arranged by type.
            :rtype: dict[type, list[NamedTuple]]
        """
        sortedDataTuples: dict[type, list[NamedTuple]] = {}
        # empty() isn't necessarily reliable due to race conditions. Neither is qsize(). Mutexes though would be even less ideal.
        # If the update rate is too high, a regular computer might not be able to keep up. maxPoints was created to exit early to process data in the intermediate moment.
        points = 0

        def binTupleIntoSortedDataTuples(dataTuple: NamedTuple):
            # Bin the tuple into the dictionary of arrays.
            dataStreamPointsList = sortedDataTuples.setdefault(type(dataTuple), [])
            dataStreamPointsList.append(dataTuple)

        try:
            while not queue.empty() and points < maxPoints: 
                try:
                    
                    dataTuple: NamedTuple | list[NamedTuple] = queue.get(block = True, timeout = 0.0001)

                    # Load it if it's not pickleable (very unsafe...). Loads in the bytestream.
                    if isinstance(dataTuple, bytes) and dill.pickles(dataTuple):
                        dataTuple = dill.loads(dataTuple)

                    # Either is a list or individualized tuples.
                    if isinstance(dataTuple, list):
                        for tupleInList in dataTuple:
                            binTupleIntoSortedDataTuples(tupleInList)
                        points += len(dataTuple)
                    else:
                        binTupleIntoSortedDataTuples(dataTuple)
                        points += 1
                except Empty:
                    pass # Explicitly silence the error.
            return sortedDataTuples
        except (ConnectionResetError, ConnectionAbortedError):
            logger.error("AnimatedGraphManager Queue was forcibly closed by remote host.")

    # Must be the same NamedTuple in the list
    def _mergeDataPointsToDataStream(self, listOfTuples: list[NamedTuple]) -> dict[str, list[float]]:
        datastreamPoints: dict[str, list[float]] = {}
        for tup in listOfTuples:
            tupleDictionary = tup._asdict() # Lop off the time parameter. 
            for property, datapoint in tupleDictionary.items():
                dataStreamPointsList = datastreamPoints.setdefault(property, [])
                dataStreamPointsList.append(datapoint)
        
        return datastreamPoints

    def _drawAnimation(self, _, fig: GraphicsLayoutWidget | Figure) -> list[Line2D | PlotDataItem]:
        # Private function that updates the graphs.
        lines = []
        datastream: DataStream
        # Figure out which configuration to draw.
        for datastream in self.datastreams.values():
            if datastream.fig == fig: # TODO: There's got to be a better way to filter these out.
                if self.realTimeType == RealTimeType.WRAPAROUND:
                    datastream.draw()
                elif self.realTimeType == RealTimeType.SLIDING_WINDOW:
                    datastream.drawSlidingWindow()
                lines.extend(datastream.getLines())
        return lines
    
    def drawFinalGraph(self, **kwargs) -> None:
        """ Draws the final graph with all of the datapoints added and with the x-axis and y-axis limits updated to fit the dataset.
        
            :param kwargs: Dictionary of keywords that should be applied to the callback function.
            :type kwargs: dict[str, Any]
            :return: None
            :rtype: None
        """

        datastream: DataStream
        for datastream in self.datastreams.values():
            datastream.drawFinal()

        for _, figureAxes in self.figureAxes.items():
            figureAxes.func(figureAxes.fig, figureAxes.ax, **kwargs) # Hook for whatever custom changes the user wants to do before showing the plot.

            if self.backend == "matplotlib":
                figureAxes.fig.canvas.draw() # This is needed for the final draw on the GUI. The plt.show() doesn't do anything.
                plt.show() # But this is needed for standalone plot drawing. The canvas is drawn, but the plt.show() keeps the figure on the screen.