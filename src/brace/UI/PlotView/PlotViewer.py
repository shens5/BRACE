from typing import Generator
from PySide6 import QtWidgets
from PySide6.QtWidgets import QApplication, QFileDialog
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
import pandas as pd
from pathlib import Path
from h5py import Group, File
from pyqtgraph.widgets.MatplotlibWidget import MatplotlibWidget
from pyqtgraph import QtCore
import numpy as np

import logging
logger = logging.getLogger("logger")

import sys
from brace.RealTimeGraphing.Graphing.DataStream import DataStream
import brace.UI.example.GUIController.PrefixNames as PrefixNames # DO NOT DELETE THIS IMPORT. This resolves the circular dependency.
from brace.UI.view.ui.Ui_PlotWindow import Ui_PlotWindow
import brace.UI.example.PlotView.PlotDataTypeHandler as PlotDataTypeHandler

class DatatypeImporter():

    @staticmethod
    def fromParquet(dataset: pd.Series) -> Generator[tuple[str, list[float | int]], None, None]:
        """
            Gets the values name of the fields and values from the parquet file (better supported). 
            The time related fields are stripped out because these values are already extracted.
        
            :param dataset: Series data from the data file. 
            :type dataset: pandas.Series

            :return: Generator containing a tuple of the name and the list of values.
            :rtype: Generator[tuple[str, list[float | int]]]
        """
        dataset[0].pop('t')
        dataset[0].pop('uptime')
        for name, values in dataset[0].items():
            yield name, values

    @staticmethod
    def fromHDF5(datagroup: Group) -> Generator[tuple[str, list[float | int]], None, None]:
        """
            Gets the values name of the fields and values from the HDF5 file (less supported). 
            The time related fields are stripped out.

            :param datagroup: The Group from the data file. 
            :type datagroup: h5py.Group

            :return: Generator containing a tuple of the name and the list of values.
            :rtype: Generator[tuple[str, list[float | int]]]
        """
        for name, values in datagroup.items():
            if name != "t":
                yield name, values
        
class PlotWindow(QtWidgets.QMainWindow, Ui_PlotWindow):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setupUi(PlotWindow = self)
        self.listOfDataHandlers = [] # Store these so that they don't get garbage collected.

    def addNewTab(self, datatype: type) -> MatplotlibWidget:
        """
            Adds a new tab containing containing a Matplotlib widget.

            :param datatype: The datatype to create a new tab to.
            :type datatype: type

            :return: The newly created widget containing the Matplotlib plot.
            :rtype: MatplotlibWidget
        """
        plotWidget = MatplotlibWidget()
        plotWidget.fig.canvas.setFocusPolicy(QtCore.Qt.ClickFocus) # Required for being able to allow key events.
        plotWidget.fig.canvas.setFocus()
        self.plotTabWidget.addTab(plotWidget, datatype.__name__)
        return plotWidget

    def getAssociatedAxes(self, dataType: type, axisMaps: dict[type, dict[str, Line2D]]) -> set[Axes]:
        """
            Gets all of the axes where at least one line is related in the datalines.

            :param dataType: The datatype to be checked for axes in the map.
            :type dataType: type
            :param axisMaps: The dictionary that organizes the lines hierarchically from type then by attribute.
            :type axisMaps: dict[type, dict[str, Line2D]]

            :return: Set of Axes that have at least one line connected to the set of dataTypes.
            :rtype: set[Axes]
        """
        associatedAxes: set[Axes] = set() # Set of subplots who have at least one line in the Datastream
        datalines: Line2D
        for datalines in axisMaps[dataType].values():
            if datalines:
                associatedAxes.add(datalines.axes)
        return associatedAxes
    
    def parseParquet(ds: pd.DataFrame, dataType: type, index: str = None, addSuffix: bool = True) -> tuple[pd.Series, pd.Series, pd.DataFrame]:
        """
            Reads in the data from the parquet file format, separating the time data and the other leg data.

            :param ds: The DataFrame containing all of the data (mixed with other datatypes)
            :type ds: pandas.DataFrame
            :param dataType: The data type to check within the DataFrame.
            :type dataType: type
            :param index: The string index that hierarchically within the datatype (e.g. "L" and "R" in left and right). 
            Default: None (indicating flat).
            :type index: str
            :param addSuffix: Appends the index as a suffix on the name of the attribute in the DataFrame (e.g. kneeAngle -> kneeAngleL). 
            Default: True 
            :type addSuffix: bool

            :return: Tuple containing the time series (Unix-epoch time and uptime) and a DataFrame containing the rest of the data.
            :rtype: tuple[pandas.Series, pandas.Series, pandas.DataFrame]
        """
        if index == None:
            legDf = pd.DataFrame.from_records(ds[dataType.__name__][0])
        else:
            legDf = pd.DataFrame.from_records(ds[dataType.__name__][0][index])
        t = legDf.pop('t')

        upTime = legDf.pop('uptime')
        if index is not None and addSuffix:
            legDf = legDf.add_suffix(index)
        return t, upTime, legDf
    
    def parseParquet2(ds: pd.DataFrame, dataType: type, index: str = None) -> pd.DataFrame:
        """
            Parses the parquet, returning all of the data without removing time or adding suffixes. Used mostly by simulation.

            :param ds: The DataFrame containing all of the data (mixed with other datatypes)
            :type ds: pandas.DataFrame
            :param dataType: The data type to check within the DataFrame.
            :type dataType: type
            :param index: The string index that hierarchically within the datatype (e.g. "L" and "R" in left and right). 
            Default: None (indicating flat).
            :type index: str

            :return: Pandas DataFrame containing the data, unaltered.
            :rtype: pandas.DataFrame
        """
        if index == None:
            legDf = pd.DataFrame.from_records(ds[dataType.__name__][0])
        else:
            legDf = pd.DataFrame.from_records(ds[dataType.__name__][0][index])
        return legDf 
    
    def parseParquetString(ds: pd.DataFrame, name: str, index: str = None) -> pd.DataFrame:
        """
            Parses the parquet file, using specifically the string instead of providing the type. Remains unaltered.

            :param ds: The DataFrame containing all of the data (mixed with other datatypes)
            :type ds: pandas.DataFrame
            :param name: The name of the data type to check within the DataFrame.
            :type dataType: str
            :param index: The string index that hierarchically within the datatype (e.g. "L" and "R" in left and right). 
            Default: None (indicating flat).
            :type index: str

            :return: Pandas DataFrame containing the data, unaltered.
            :rtype: pandas.DataFrame
        """
        if index == None:
            legDf = pd.DataFrame.from_records(ds[name][0])
        else:
            legDf = pd.DataFrame.from_records(ds[name][0][index])
        return legDf 

    def checkParquetIndex(ds: pd.DataFrame, dataType: type, index: str = None) -> bool:
        """
            Checks whether or not the index is found in the parquet file.

            :param ds: The DataFrame containing all of the data (mixed with other datatypes)
            :type ds: pandas.DataFrame
            :param name: The name of the data type to check within the DataFrame.
            :type dataType: str
            :param index: The string index that hierarchically within the datatype (e.g. "L" and "R" in left and right). 
            Default: None (indicating flat).
            :type index: str

            :return: Whether or not the index is in the DataFrame.
            :rtype: bool
        """
        if index is None:
            return isinstance(ds[dataType.__name__][0], np.ndarray)
        else:
            return index in ds[dataType.__name__][0] and ds[dataType.__name__][0][index] is not None
        
    def graphLegDataParquet(self, fig: Figure, axisMaps: dict[type, dict[str, Line2D]], dataType: type, ds: pd.DataFrame) -> None:
        """
            Graphs the data from the parquet file by updating the datastreams to include the datapoints.

            :param fig: The Figure containing all the axes.
            :type fig: matplotlib.Figure
            :param axisMaps: The dictionary that organizes the lines hierarchically from type then by attribute.
            :type axisMaps: dict[type, dict[str, Line2D]]
            :param dataType: The data type that should be graphed on the axes.
            :type dataType: type
            :param ds: The DataFrame containing all of the data.
            :type ds: pandas.DataFrame

            :return: None
            :rtype: None
        """
        associatedAxes = list(self.getAssociatedAxes(dataType, axisMaps))
        datastream = DataStream(fig, associatedAxes, axisMaps[dataType], dataType)

        if PlotWindow.checkParquetIndex(ds, dataType, 'L'):
            t, _, leftLeg = PlotWindow.parseParquet(ds, dataType, 'L')
            for name, values in leftLeg.items():
                datastream.updatePoints(name, t, values) # Some lines are not drawn, but are included in the dataset.
        
        if PlotWindow.checkParquetIndex(ds, dataType, 'R'):
            t, _, rightLeg = PlotWindow.parseParquet(ds, dataType, 'R')
            for name, values in rightLeg.items():
                datastream.updatePoints(name, t, values) # Some lines are not drawn, but are included in the dataset.

        # This handles the Trigger, but would work against data that does not have any L and R associated to it.
        if PlotWindow.checkParquetIndex(ds, dataType):
            t, _, singleData = PlotWindow.parseParquet(ds, dataType)
            for name, values in singleData.items():
                datastream.updatePoints(name, t, values) # Some lines are not drawn, but are included in the dataset.
        datastream.updateTime(t)
        datastream.drawFinal(padding = 0.05)

    def graphLegDataHdf5(self, fig: Figure, axisMaps: dict[type, dict[str, Line2D]], dataType: type, hdfS: pd.HDFStore) -> None:
        """
            Graphs the data from the HDF5 file by updating the datastreams to include the datapoints.

            :param fig: The Figure containing all the axes.
            :type fig: matplotlib.Figure
            :param axisMaps: The dictionary that organizes the lines hierarchically from type then by attribute.
            :type axisMaps: dict[type, dict[str, Line2D]]
            :param dataType: The data type that should be graphed on the axes.
            :type dataType: type
            :param ds: The HDFStore containing all of the data.
            :type ds: pandas.HDFStore
            
            :return: None
            :rtype: None
        """
        associatedAxes = list(self.getAssociatedAxes(dataType, axisMaps))
        datastream = DataStream(fig, associatedAxes, axisMaps[dataType], dataType)

        if f'/{dataType.__name__}/L' in list(hdfS) \
                and (leftLeg := hdfS.get(f'{dataType.__name__}/L')) is not None and not leftLeg.isna().values.all():
            t = leftLeg.pop('t')
            _ = leftLeg.pop('uptime')
            leftLeg = leftLeg.add_suffix("L")
            for name, values in leftLeg.items():
                datastream.updatePoints(name, t, values) # Some lines are not drawn, but are included in the dataset.
        
        if f'/{dataType.__name__}/R' in list(hdfS) \
                and (rightLeg := hdfS.get(f'{dataType.__name__}/R')) is not None and not rightLeg.isna().values.all():
            t = rightLeg.pop('t')
            _ = rightLeg.pop('uptime')
            rightLeg = rightLeg.add_suffix("R")
            for name, values in rightLeg.items():
                datastream.updatePoints(name, t, values) # Some lines are not drawn, but are included in the dataset.

        # This handles the Trigger, but would work against data that does not have any L and R associated to it.
        if f'/{dataType.__name__}' in list(hdfS) and isinstance(hdfS[dataType.__name__], pd.DataFrame):
            singleData = hdfS.get(dataType.__name__)
            t = singleData.pop('t')
            _ = singleData.pop('uptime')
            for name, values in singleData.items():
                datastream.updatePoints(name, t, values) # Some lines are not drawn, but are included in the dataset.
        datastream.updateTime(t)
        datastream.drawFinal(padding = 0.05)
    
    def openDataset(self) -> None:
        """
            Main function that opens a file dialog to input a file. 
            Then opens the dataset and graphs the data. Currently ".parquet" and ".h5" are supported,
            with parquet files being supported the best.

            :return: None
            :rtype: None
        """
        options = QFileDialog.Option() # Must use DontUseNativeDialog for other options to work.
        openDatasetFileDialog = QFileDialog(self)
        fileName, _ = openDatasetFileDialog.getOpenFileName(self, "Load Dataset File", 
                                                           "", "Parquet Files (*.parquet);;HDF5 Files (*.h5)", options = options)
        self.setWindowTitle(f"{self.windowTitle()} - {fileName}")
        fileNameSuffix = Path(fileName).suffix

        # Parse dataset and graph.        
        if fileNameSuffix == ".parquet":
            ds = pd.read_parquet(fileName)

            try:
                listOfDatatypes = ds.columns.to_list()
                configDictionary = None
                if 'Configuration' in listOfDatatypes:
                    listOfDatatypes.remove('Configuration')
                    configDictionary = ds['Configuration'][0]
                
                if 'APIEvents' in self.listOfDataHandlers:
                    listOfDatatypes.remove('APIEvents') # API Events for simulation, remove these for viewing.
                
                for datatypeName in listOfDatatypes:
                    # Get relevant configuration values that may be present.
                    # Set up the figures, axis, and axis maps on new tab.
                    # Update all the values in the axis (only need 1 set of time values though).
                    dataTypeHandler = PlotDataTypeHandler.getDataTypeHandler(datatypeName)                   
                    if dataTypeHandler is not None:
                        plotWidget = self.addNewTab(dataTypeHandler.DataType)
                        configurationToDisplay = dataTypeHandler.getConfigurableValues(configDictionary)
                        configurePlotObject = dataTypeHandler.configurePlots(plotWidget, configurationToDisplay)
                        self.listOfDataHandlers.append(configurePlotObject)
                        fig, ax, axisMaps = self.listOfDataHandlers[-1].getFigureAxesAxesMapTriple()
                        self.graphLegDataParquet(fig, axisMaps, dataTypeHandler.DataType, ds)
                        dataTypeHandler.updateFinalPlot(configurePlotObject)

            except ValueError as e:
                logger.error(e)

        elif fileNameSuffix == ".h5":
            with pd.HDFStore(fileName, 'r') as f:
                listOfDatatypes = list({Path(name).parts[1] for name in list(f)})
                configDictionary = None
                if 'Configuration' in listOfDatatypes:
                    listOfDatatypes.remove('Configuration')
                    configDictionary = dict(f['Configuration'])

                if 'APIEvents' in listOfDatatypes:
                    listOfDatatypes.remove('APIEvents') # API Events for simulation, remove these for viewing.

                for datatypeName in listOfDatatypes:
                    # Get relevant configuration values that may be present.
                    # Set up the figures, axis, and axis maps on new tab.
                    # Update all the values in the axis (only need 1 set of time values though).
                    dataTypeHandler = PlotDataTypeHandler.getDataTypeHandler(datatypeName)                   
                    if dataTypeHandler is not None:
                        plotWidget = self.addNewTab(dataTypeHandler.DataType)
                        configurationToDisplay = dataTypeHandler.getConfigurableValues(configDictionary)
                        configurePlotObject = dataTypeHandler.configurePlots(plotWidget, configurationToDisplay)
                        self.listOfDataHandlers.append(configurePlotObject)
                        fig, ax, axisMaps = self.listOfDataHandlers[-1].getFigureAxesAxesMapTriple()
                        self.graphLegDataHdf5(fig, axisMaps, dataTypeHandler.DataType, f)
                        dataTypeHandler.updateFinalPlot(configurePlotObject)
                        
def main():
    logger.setLevel(logging.DEBUG)  # Logger debug has to be set to the "lowest" level
    formatter = logging.Formatter(fmt = "%(asctime)s.%(msecs)03d %(levelname)s: %(message)s", 
                                  datefmt = "%Y-%m-%d %H:%M:%S")
    
    app = QApplication(sys.argv)
    mainWindow = PlotWindow()
    mainWindow.openDataset()
    mainWindow.show()

    sys.exit(app.exec())
    
if __name__ == '__main__':
    logger = logging.getLogger("logger")
    main()