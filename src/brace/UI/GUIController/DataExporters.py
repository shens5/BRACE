from __future__ import annotations
from abc import ABC, abstractmethod
import pandas as pd
import numpy as np
import json
from typing import override

from typing import TYPE_CHECKING, Generator
if TYPE_CHECKING:
    from brace.RealTimeGraphing.Graphing.AnimatedGraphManager import AnimatedGraphManager
    from brace.UI.example.MainWindow import MainWindow
import logging
logger = logging.getLogger("logger")

def formatLeftRight(datastreamData: dict[str, list[float| int]]) -> tuple[dict[str, list[float| int]], dict[str, list[float| int]]]:
    """
        Formats the data into left and right based on the L or R at the end of the name of the attribute.
        If there is no L or R, then the value goes to both legs.

        :param datastreamData: Data formatted in a dictionary of a list of floats or ints.
        :type datastreamData: dict[str, list[float | int]]
        :return: Data sorted into left and right dictionaries by the attribute name.
        :rtype: tuple[dict[str, list[float | int], dict[str, list[float | int]]]]
    """
    # Attributes that have L go into leftAttributes. Attributes that have R go to rightAttributes. Ones that have neither go to both.
    leftAttributes = {}
    rightAttributes = {}

    keysWithLeftRight = set()
    keysWithNeither = set() 

    # Sort attributes based on the L and R characteristic (or not).
    datastreamKeys = datastreamData.keys()
    for datastreamKey in datastreamKeys:
        if datastreamKey.endswith("L") or datastreamKey.endswith("R"):
            keyPrefix = datastreamKey[0:-1]
            if f"{keyPrefix}R" in datastreamKeys and f"{keyPrefix}L" in datastreamKeys:
                keysWithLeftRight.add(keyPrefix)
        else:
            keysWithNeither.add(datastreamKey)

    # Add the respective datalines to the dictionaries with L and R.
    leftAttributes = { datastreamPrefix: datastreamData[f"{datastreamPrefix}L"] for datastreamPrefix in keysWithLeftRight }
    rightAttributes = { datastreamPrefix: datastreamData[f"{datastreamPrefix}R"] for datastreamPrefix in keysWithLeftRight }
    
    # And if it doesn't have either L and R, then both of the dictionaries get the value.
    for neitherKey in keysWithNeither:
        leftAttributes[neitherKey] = datastreamData[neitherKey]
        rightAttributes[neitherKey] = datastreamData[neitherKey]
    return leftAttributes, rightAttributes

def isNanDatastream(datastream: dict[str, list[float| int]]) -> bool:
    """
        Checks if the datastream given for a left or right leg is NaN.
    
        :params datastream: The left or right leg datastream
        :type datastream: dict[str, list[float | int]]
        :return: Whether or not the datastream only has NaNs.
        :rtype: bool
    """
    datastreamToCheck = datastream.copy() # Make sure not to modify the dictionary
    _ = datastreamToCheck.pop('t') # Remove time (since those will always be active values)
    _ = datastreamToCheck.pop('uptime') # Remove time (since those will always be active values)
    for datalineName, dataline in datastreamToCheck.items():
        if not np.isnan(dataline).all():
            return False
    return True

class AbstractDataExporter(ABC):
    """
        An abstract class that exports the datastreams into a certain format.
    """
    def __init__(self):
        super().__init__()

    def exportDatastreamData(self, animatedGraphManager: AnimatedGraphManager, startStreamUnixTime: float) -> Generator[type, dict[str, list[float| int]]]:
        """
            A helper that yields the type and the datastream data from the datastreams of an AnimatedGraphManager.
            Two times are listed, "t" which refers to the time offset to the local time which may be less precise (but useful for general times).
            Or "uptime" which should be used for all analyses as this time is offset from the beginning of the stream time (and is more precise).

            :param animatedGraphManager: The AnimatedGraphManager whose data should be exported.
            :type animatedGraphManager: AnimatedGraphManager
            :param startStreamUnixTime: The local time of the time when the datastream was started (in seconds).
            :type startStreamUnixTime: float

            :return: A generator containing a tuple of the type and the data of that datastream.
            :rtype: Generator[type, dict[str, list[float | int]]]
        """
        datastreamData = {}
        for datastreamType, datastream in animatedGraphManager.datastreams.items():
            if len(datastream.t) != 0: # Exclude any datatypes that don't have any data.
                datastreamData = {}
                datastreamData['t'] = list(pd.to_datetime(list(map(lambda t: t + startStreamUnixTime, datastream.t)), unit = 's')) # Crazy back and forth conversion to format correctly.
                datastreamData['uptime'] = datastream.t
                for dataline in datastream.getDatalines():
                    datastreamData[dataline.propertyName] = dataline.yData.values()
                yield datastreamType, datastreamData

    @abstractmethod
    def exportData(self, animatedGraphManager: AnimatedGraphManager, filename: str, startStreamUnixTime: float, controlLogicEnumType: type, parent: MainWindow = None) -> None:
        """
            An abstract method that should be implemented by all exporting classes, which formats the dataset into
            the desired data structure and file format.
        
            :param animatedGraphManager: The AnimatedGraphManager to export data.
            :type animatedGraphManager: AnimatedGraphManager
            :param filename: The filename to export the data into.
            :type filename: str
            :param startStreamUnixTime: The starting time (referenced against Unix epoch) at which the stream has started.
            :type startStreamUnixTime: float
            :param controlLogicEnumType: The enum type the control logic that is to checked against the remote (for configuration).
            :type controlLogicEnumType: type
            :param parent: The main GUI that is exporting the data.
            :type parent: MainWindow
            
            :return: None
            :rtype: None
        """
        pass

class ParquetExporter(AbstractDataExporter):
    def __init__(self):
        super().__init__()
            
    @override
    def exportData(self, animatedGraphManager: AnimatedGraphManager, filename: str, startStreamUnixTime: float, controlLogicEnumType: type, parent: MainWindow = None) -> None:
        """
            Exports the data in the parquet file format, hierarchically setting the data in "L" and "R" paths,
            scrunching down the table into a single column to fit in the row of a parquet file. Configuration and APIEvents
            are also first-class attributes of this file format (as metadata).

            :param animatedGraphManager: The AnimatedGraphManager to export data.
            :type animatedGraphManager: AnimatedGraphManager
            :param filename: The filename to export the data into.
            :type filename: str
            :param startStreamUnixTime: The starting time (referenced against Unix epoch) at which the stream has started.
            :type startStreamUnixTime: float
            :param controlLogicEnumType: The enum type the control logic that is to checked against the remote (for configuration).
            :type controlLogicEnumType: type
            :param parent: The main GUI that is exporting the data.
            :type parent: MainWindow
            
            :return: None
            :rtype: None
        """
        dataStreams = self.exportDatastreamData(animatedGraphManager, startStreamUnixTime)
        totalDatasets = {}
        dataStreamConfiguration = {}
        eventStream = []
        
        for dataStreamType, datastreamData in dataStreams:
            
            leftDatastream, rightDatastream = formatLeftRight(datastreamData = datastreamData)
            
            if leftDatastream == rightDatastream: # Two are equal, as in the case of Trigger
                dataframe = pd.DataFrame(leftDatastream)
                totalDatasets[dataStreamType] = [dataframe.to_dict(orient = 'records')] # Convert from columns to list of dictionary rows.
            else:
                # Check if they are active, i.e. the data isn't just a bunch of NaNs.
                isLeftActive = not isNanDatastream(leftDatastream)
                isRightActive = not isNanDatastream(rightDatastream)

                leftDataframe = pd.DataFrame(leftDatastream)
                rightDataframe = pd.DataFrame(rightDatastream)

                # Format like a tree, L and R with their own elements and t as a table. If inactive, it's a row with a NaN.
                # to_dict with orient 'records' converts it to a list of dictionaries instead of a dictionary of lists.
                leftDataToShow = leftDataframe.to_dict(orient = 'records') if isLeftActive else np.nan
                rightDataToShow = rightDataframe.to_dict(orient = 'records') if isRightActive else np.nan

                if parent is not None: # Should be the MainWindow
                    remoteConfiguration = parent.readControllerConfigurationRemote(controlLogicEnumType[str(dataStreamType).upper()], True)
                    if remoteConfiguration:
                        leftConfiguration, rightConfiguration = remoteConfiguration
                        leftConfigurationToAdd = leftConfiguration if isLeftActive else np.nan
                        rightConfigurationToAdd = rightConfiguration if isRightActive else np.nan
                        leftRightConfiguration = {"L": leftConfigurationToAdd, "R": rightConfigurationToAdd}
                        dataStreamConfiguration[dataStreamType] = leftRightConfiguration
                    else:
                        logger.error("Failed to get configuration from remote. Configuration information will not be in the data file.")
                totalDatasets[dataStreamType] = [{"L": leftDataToShow, "R": rightDataToShow}]

        # Create separate part for API Events; remote procedure calls.
        if parent is not None and (eventStream := parent.readControllerApiEvents()):
            convertedEventStream = []
            for uptime, functionName, functionParameters in eventStream:
                functionParametersToAdd = json.dumps(functionParameters)
                convertedEventStream.append({'uptime': uptime, 'functionName': functionName, 'functionParameters': functionParametersToAdd})

            totalDatasets["APIEvents"] = [convertedEventStream]
        else:
            totalDatasets["APIEvents"] = [np.nan]

        if parent is not None and dataStreamConfiguration:
            # Parquet files do have a metadata area where custom information can be stored, but Matlab isn't able to
            # read this metadata out of the box. Thus, Configuration information is listed as a first class data element of the dataset.
            totalDatasets["Configuration"] = [dataStreamConfiguration]

        dataframeToExport = pd.DataFrame(totalDatasets)
        dataframeToExport.to_parquet(filename, engine = 'pyarrow')
        logger.info(f"Data was saved to {filename}, with file format Parquet.")

class HDF5Exporter(AbstractDataExporter):
    def __init__(self):
        super().__init__()

    @override
    def exportData(self, animatedGraphManager: AnimatedGraphManager, filename: str, startStreamUnixTime: float, controlLogicEnumType: type, parent: MainWindow = None) -> None:
        dataStreams = self.exportDatastreamData(animatedGraphManager, startStreamUnixTime)
        dataStreamConfiguration = {}
        with pd.HDFStore(filename, 'w') as store:
            dataStreamType: type
            for dataStreamType, datastreamData in dataStreams:
                leftDatastream, rightDatastream = formatLeftRight(datastreamData = datastreamData)
                isLeftActive = not isNanDatastream(leftDatastream)
                isRightActive = not isNanDatastream(rightDatastream)
                leftConfiguration, rightConfiguration = None, None

                if leftDatastream == rightDatastream: # Two are equal, as in the case of Trigger
                    store.put(f'{dataStreamType}', pd.DataFrame(leftDatastream), format='table')
                else:
                    if parent is not None: # Should be the MainWindow
                        remoteConfiguration = parent.readControllerConfigurationRemote(controlLogicEnumType[str(dataStreamType).upper()], True)
                        if remoteConfiguration:
                            leftConfiguration, rightConfiguration = remoteConfiguration
                            leftConfigurationToAdd = leftConfiguration if isLeftActive else np.nan
                            rightConfigurationToAdd = rightConfiguration if isRightActive else np.nan
                            leftRightConfiguration = {"L": leftConfigurationToAdd, "R": rightConfigurationToAdd}
                            dataStreamConfiguration[dataStreamType] = leftRightConfiguration
                        else:
                            logger.error("Failed to get configuration from remote. Configuration information will not be in the data file.")
                    
                    store.put(f'{dataStreamType}/L', pd.DataFrame(leftDatastream) if isLeftActive else pd.DataFrame([np.nan]), format = 'table')
                    store.put(f'{dataStreamType}/R', pd.DataFrame(rightDatastream) if isRightActive else pd.DataFrame([np.nan]), format = 'table')
                    
            if parent is not None and dataStreamConfiguration:
                # pandas h5 vs h5py is tricky in the balance of tools.
                # h5py has metadata, but dealing with timestamped items is a little less streamlined than pandas.
                # On the other hand, pandas doesn't have a great way of storing metadata.
                # In lieu of this, storing it as a first class member is possible (like done with the parquet file), but PerformanceWarnings happen
                # with nested dictionaries. These aren't full datasets though, it might be okay to ignore the warning.
                store.put(f'Configuration', pd.DataFrame(dataStreamConfiguration))
        logger.info(f"Data was saved to {filename}, with file format HDF5.")