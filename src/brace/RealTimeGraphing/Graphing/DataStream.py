from collections import deque
import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from matplotlib.lines import Line2D
from matplotlib.figure import Figure
import numpy as np
from pyqtgraph import PlotDataItem, PlotItem, GraphicsLayoutWidget
from sortedcontainers import SortedDict, SortedList
from threading import RLock
from heapq import merge

class DataLine():
    """
        Class that plots the lines on the graph identifying with NamedTuple fields.
    """
    def __init__(self, line: Line2D | PlotDataItem, propertyName: str, backend: str = 'matplotlib'):
        """
            :param line: The line that is to be drawn using the datapoints.
            :type line: Line2D | PlotDataItem
            :param propertyName: The field name of the NamedTuple identifying this line.
            :type propertyName: str
            :param backend: String identifying as 'matplotlib' or 'pyqtgraph'
            :type backend: str
        """
        self.yData = SortedDict()
        self.line = line
        self.propertyName = propertyName
        self.backend = backend
        self.updateLock = RLock()
        self.timesNaN = []

        self.lastDrawnIndex = 0
        self.drawYValues = deque()
        self.drawTValues = deque()

    def getPropertyName(self) -> str:
        """
            Returns the field name of the line, that is based on the NamedTuple name.

            :return: The field name of NamedTuple that belongs to this line.
            :rtype: str
        """
        return self.propertyName
    
    def clearDataLine(self) -> None:
        """
            Clears out all the data in this line including all caches and stored data.
            
            :return: None
            :rtype: None
        """
        if self.line is not None:
            self.line.clear()
        self.yData.clear()
        self.drawTValues.clear()
        self.drawYValues.clear()
        self.timesNaN.clear()
        self.lastDrawnIndex = 0

    def getLine(self) -> Line2D | PlotDataItem:
        """
            Gets the line element for this DataLine that draws in the plot.

            :return: The line element that draws in the plots.
            :rtype: Line2D | PlotDataItem
        """
        return self.line
    
    def updatePoints(self, t: np.ndarray[float], y: np.ndarray[float]) -> None:
        """ 
            Updates the internally listed datapoints and the lines for each related dataset.

            :param t: A list of data indicating the time component that should be paired with the y-axis data.
            :type t: np.ndarray[float] | list[float]
            :param y: : A list of data that should be paired with the time series which is stored and 
                can be plotted against the axis lines. 
            :type y: np.ndarray[float] | list[float]
            :return: None
            :rtype: None
        """
        # Update the data
        with self.updateLock as lock:
            for timeData, yData in zip(t, y):
                if yData is None:
                    self.yData[timeData] = np.nan
                    self.timesNaN.append(timeData)
                else:
                    self.yData[timeData] = yData

    def updateLine(self, startingIndex: int, sampleNumber: int) -> None:
        """
            Updates the line based on a starting index and goes to the end of the array, sampling
            1:sampleNumber for the time series datasets. The last element is plotted. This
            type of plotting is generally used for the "wraparound" type plots.

            :param startingIndex: The index of the data that should be started for plotting.
            :type startingIndex: int
            :param sampleNumber: How many elements to skip before the next sample is plotted.
            :type sampleNumber: int
            :return: None
            :rtype: None
        """
        # Sample the data by every SAMPLE_NUMBER between the start and end points.
        timeData = list(self.yData.keys()[startingIndex::sampleNumber])
        yData = list(self.yData.values()[startingIndex::sampleNumber])

        # Add in the last element to maintain up-to-dateness with the plot. If available.
        if (timeData and yData) and (len(timeData) < len(self.yData)) and (len(yData) < len(self.yData)):
            timeData.append(self.yData.keys()[-1])
            yData.append(self.yData.values()[-1])

        if self.line and (len(timeData) == len(yData)) and (not np.isnan(yData).all()):
            if self.backend == 'matplotlib':
                self.line.set_data(timeData, yData)
            elif self.backend == 'pyqtgraph':
                self.line.setData(timeData, yData)
    
    # t is a list of times that should be drawn.
    def updateLine2(self, startingIndex: int, sampleNumber: int) -> None:
        """
            Updates the line based on a starting index and goes to the end of the array, sampling
            1:sampleNumber for the time series datasets, caching it frame-by-frame for performance.
            The last element is plotted. This type of plotting is generally used for the "sliding window" type plots.

            :param startingIndex: The index of the data that should be started for plotting.
            :type startingIndex: int
            :param sampleNumber: How many elements to skip before the next sample is plotted.
            :type sampleNumber: int
            :return: None
            :rtype: None
        """
        # with self.updateLock as lock:
        numberOfSamplesToAdd = (len(self.yData) - self.lastDrawnIndex) // sampleNumber
        timesToAdd = merge([self.yData.keys()[self.lastDrawnIndex + (i * sampleNumber)] for i in range(numberOfSamplesToAdd)], self.timesNaN)        
        # for i in range(0, numberOfSamplesToAdd):
        #     self.drawTValues.append(self.yData.keys()[self.lastDrawnIndex + (i * sampleNumber)])
        #     self.drawYValues.append(self.yData.values()[self.lastDrawnIndex + (i * sampleNumber)])
        for time in timesToAdd:
            self.drawTValues.append(time)
            self.drawYValues.append(self.yData[time])
        
        # Need to have separate case if there is a NaN, otherwise it may continue to get an index
        # that is before the NaN which then continues to draw an erroneous line because it is chronologically before the point.
        if self.timesNaN: # Easy enough to just reset the index to the NaN position. Though this may not scale very well (keep to minimum)
            self.lastDrawnIndex = list(self.yData.keys()).index(self.timesNaN[-1])
        else:
            self.lastDrawnIndex = self.lastDrawnIndex + (numberOfSamplesToAdd * sampleNumber) 
        self.timesNaN.clear()

        # Remove the t values at the beginning that are past the timeStart.
        if self.drawTValues and self.drawYValues:
            timeStart = self.yData.keys()[startingIndex]
            while len(self.drawTValues) != 0 and self.drawTValues[0] < timeStart:
                self.drawTValues.popleft()
                self.drawYValues.popleft()

        timeData = self.drawTValues
        yData = self.drawYValues

        # Add the last value at the end.
        if (len(timeData) > 0 and len(yData) > 0) and (len(timeData) < len(self.yData)) and (len(yData) < len(self.yData)):
            with self.updateLock as lock:
                tValue, yValue = self.yData.items()[-1]
                timeData = np.array([*timeData, tValue])
                yData = np.array([*yData, yValue])

        # Set the data for the line.
        if self.line and (len(timeData) == len(yData)) and (not np.isnan(yData).all()):
            if self.backend == 'matplotlib':
                self.line.set_data(timeData, yData)
            elif self.backend == 'pyqtgraph':
                self.line.setData(timeData, yData)


class DataStream():
    """
        A class that bridges the figure drawing from the lines and the NamedTuple that is
        assigned to the lines. 
    """

    def __init__(self, fig: GraphicsLayoutWidget | Figure, axes: list[Axes] | list[PlotItem], lines: dict[str, Line2D] | dict[str, PlotDataItem], namedTupleType: type, 
                 graphDownSampleRate: int = 20, MAX_TIME_RANGE: float = 10, backend: str = "matplotlib"):
        """
            :param fig: The Figure or GraphicsLayoutWidget that contains the plots to be drawn.
            :type fig: GraphicsLayoutWidget | Figure
            :param axes: The plots that should be updated and drawn.
            :type axes: list[Axes] | list[PlotItem]
            :param lines: Dictionary that assigns the NamedTuple field names by line.
            :type lines: dict[str, Line2D]
            :param namedTupleType: The NamedTuple type whose data should be graphed.
            :type namedTupleType: type
            :param graphDownSampleRate: The number of points in between samples before another point is drawn. Must be greater than 0, default is 20.
            :type graphDownSampleRate: int
            :param MAX_TIME_RANGE: The maximum range of points temporally from the initial start sampling point that should be drawn. Default is 10 (seconds).
            :type MAX_TIME_RANGE: float
            :param backend: The type of plots that are using this drawing system. Either 'matplotlib' or 'pyqtgraph'
            :type backend: str
        """
        self.fig = fig
        self.dataLines: dict[str, DataLine] = {}
        self.t: SortedList[float] = SortedList()
        for propertyName, line in lines.items():
            self.dataLines[propertyName] = DataLine(line, propertyName, backend)
        self.namedTupleType = namedTupleType.__name__
        self.graphingDownSampleRate = graphDownSampleRate
        self.axes = axes
        self.MAX_TIME_RANGE = MAX_TIME_RANGE

        self.plotIndex = 0
        self.backend = backend

    def getDatalines(self) -> list[DataLine]:
        """
            Gets the point/line relations between the plots.

            :return: The list of DataLines for this DataStream object
            :rtype: list[DataLine]
        """
        return list(self.dataLines.values())
     
    def clearData(self) -> None:
        """
            Clears out the data in all the datalines and in the time list.
            Indexing for the plots is reset back to the beginning.
        
            :return: None
            :rtype: None
        """
        for dataline in self.dataLines.values():
            dataline.clearDataLine()
        self.t.clear()
        self.plotIndex = 0
            
    def updateTime(self, timePoints: list[float]) -> None:
        """
            Updates the time points with new data (high level)

            :param timePoints: list of time points to append to the end.
            :type timePoints: list[float]
            :return: None
            :rtype: None
        """
        self.t.update(timePoints)

    def updatePoints(self, property: str, tPoints: list[float], dataPoints: list[float]) -> None:
        """
            Updates the data points with new data (low level) for the dataLines

            :param property: The NamedTuple field name that should be updated with the new data points.
            :type property: str
            :param tPoints: The time list of points to update.
            :type tPoints: list[float]
            :param dataPoints: The y-axis points that should be aligned with the tPoints.
            :type dataPoints: list[float]
            :return: None
            :rtype: None
        """
        self.dataLines[property].updatePoints(tPoints, dataPoints)

    def getLines(self) -> list[Line2D] | list[PlotDataItem]:
        """
            Gets the individual list of lines that should have data plotted.

            :return: List of lines that plot datapoints.
            :rtype: list[Line2D] | list[PlotDataItem]
        """
        listOfLines = []
        for dataline in self.dataLines.values():
            line = dataline.getLine()
            if line:
                listOfLines.append(line)
        return listOfLines

    # Option for a sliding window-type real time plot.
    def drawSlidingWindow(self) -> None:
        """ 
            Draws the plot in the sliding window-type configuration. Determines the window where the
            furthest right refers to the most immediate datapoint that was added, and the furthest left
            is the datapoint from t[-1] - MAX_TIME_RANGE forward. If there are no datapoints from that
            range nothing is drawn, but the x-axis limits are still set to this window.

            :return: None
            :rtype: None
        """
        if self.t:
            while self.t[self.plotIndex] < self.t[-1] - self.MAX_TIME_RANGE and (self.plotIndex + self.graphingDownSampleRate < len(self.t)):
                self.plotIndex += self.graphingDownSampleRate
            
            for dataline in self.dataLines.values(): 
                dataline.updateLine2(self.plotIndex, self.graphingDownSampleRate)

            leftTimeRange = min(self.t[-1] - self.MAX_TIME_RANGE, self.t[self.plotIndex])
            for axis in self.axes:
                if self.backend == 'matplotlib':
                    # Shift the x-limits so that it scrolls correctly.
                    axis.set_xlim(leftTimeRange, self.t[-1])
                elif self.backend == 'pyqtgraph':
                    [[xLeft, xRight], [_, _]] = axis.viewRange()
                    # A kind of cool trick to optimize the amount number of times it needs to set the x range (not done every call)
                    # This allows you to still have scrolling x axis while still maintaining frame rates.
                    if leftTimeRange - xLeft > (leftTimeRange - xLeft) * 0.25 and self.t[-1] - xRight > (self.t[-1] - xRight) * 0.25:
                        axis.setXRange(leftTimeRange, self.t[-1], padding = 0.0)

    
    # Option for "reach the right side before wrapping around" real time plot
    def draw(self) -> None:
        """ 
            Draws the plot in the wraparound configuration. If the last datapoint has a time that reaches beyond a multiple
            of the MAX_TIME_RANGE, then it will refresh and adjust the x-axis limits as needed so that the plotting can continue
            from the furthest left onwards.

            :return: None
            :rtype: None
        """
        if self.t:
            lastT = self.t[-1]
            axisChange = False

            # Two cases where we want to change the range:
            # 1) Push the starting index forward if reached the entire right side.
            # 2) The range is not situated in a meaningful area that shows the data.
            if lastT >= self.t[self.plotIndex] + self.MAX_TIME_RANGE:
                self.plotIndex = len(self.t) - 1
                axisChange = True
            else:
                for axis in self.axes:
                    if self.backend == 'matplotlib':
                        xLeft, xRight = axis.get_xlim()
                    elif self.backend == 'pyqtgraph':
                        [[xLeft, xRight], [_, _]] = axis.viewRange()
                        
                    if xLeft != self.t[self.plotIndex] or xRight != xLeft + self.MAX_TIME_RANGE:
                        axisChange = True
                        break

            for dataline in self.dataLines.values(): 
                dataline.updateLine(self.plotIndex, self.graphingDownSampleRate)
                
            if axisChange:
                for axis in self.axes:
                    if self.backend == 'matplotlib':
                        axis.set_xlim(self.t[self.plotIndex], self.t[self.plotIndex] + self.MAX_TIME_RANGE)
                    elif self.backend == 'pyqtgraph':
                        axis.setXRange(self.t[self.plotIndex], self.t[self.plotIndex] + self.MAX_TIME_RANGE, padding = 0.0)

    def drawFinal(self, padding: float = 0.00) -> None:
        """ 
            Draws the plot in the final draw configuration. This contains all of the datapoints and updates the 
            x-axis and y-axis limits so that it fits the minimum and maximum values of each of the datasets.

            :param padding: The percentage padding that should be included in the plots after the final draw. Default is 0.00,
                indicating hard fit.
            :type padding: float
            :return: None
            :rtype: None
        """

        # Update the lines with all of the data collected.
        self.plotIndex = 0
        for dataline in self.dataLines.values():
            dataline.updateLine(startingIndex = 0, sampleNumber = 1)
        
        # Set axis limits based on min/max of the x and y values.
        for axis in self.axes:
            if self.backend == 'matplotlib':
                allYData = [] # Includes the axhlines too (two datapoints).
                for data in axis.get_lines():
                    yData = data.get_ydata()
                    if len(yData) > 0 and not np.isnan(yData).all(): # Excludes empty lists and ones with all NaNs.
                        allYData.append(yData) 
            elif self.backend == 'pyqtgraph':
                allYData = []
                for data in axis.listDataItems():
                    xData, yData = data.getData()
                    if yData is not None and not np.isnan(yData).all(): # In pyqtgraph None represents the empty y set.
                        allYData.append(yData)

            if allYData and self.t:
                yMin, yMax = float(min(map(np.nanmin, allYData))), float(max(map(np.nanmax, allYData))) # np.min/max preferable, but non-homogenous dimensions not guaranteed
                xMin, xMax = np.min(self.t), np.max(self.t)

                paddingDistanceY = yMax - yMin if yMin != yMax else 1.0 # Create a padding distance that is non-zero, which forces Matplotlib to work.
                paddingDistanceX = xMax - xMin if xMin != xMax else 1.0

                # Add some padding so that the graphs don't fit too tightly to the max and min.
                yMin -= abs(padding * (paddingDistanceY))
                yMax += abs(padding * (paddingDistanceY))
                xMin -= abs(padding * (paddingDistanceX))
                xMax += abs(padding * (paddingDistanceX))

                if self.backend == 'matplotlib':
                    if yMin != yMax:
                        axis.set_ylim(yMin, yMax)
                    if xMin != xMax:
                        axis.set_xlim(xMin, xMax)
                elif self.backend == 'pyqtgraph':
                    if yMin != yMax:
                        axis.setYRange(yMin, yMax)
                    if xMin != xMax:
                        axis.setXRange(xMin, xMax)