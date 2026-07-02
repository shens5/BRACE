from __future__ import annotations
from datetime import datetime
import pathlib
from PySide6.QtCore import Slot
from PySide6.QtWidgets import QDialog, QFileDialog, QWidget
from brace.UI.view.ui.Ui_SaveDialog import Ui_SaveDialog
from brace.UI.GUIController.DataExporters import AbstractDataExporter, ParquetExporter, HDF5Exporter
from functools import partial
import logging
from brace.RealTimeGraphing.Graphing.AnimatedGraphManager import AnimatedGraphManager
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from brace.UI.example.MainWindow import MainWindow
logger = logging.getLogger("logger")

class SaveDialog(Ui_SaveDialog, QDialog):
    """
        This dialog box is shown when the user stops streaming. It will
        ask the user whether or not the streamed data should be saved before
        enacting on the user decision.
    """
    """Save dialog used for saving the streamed data"""
    def __init__(self, parent: MainWindow, animatedGraphManager: AnimatedGraphManager, startStreamUnixTime: float, controlLogicEnumType: type):
        """
            :param parent: The parent saving GUI that runs this dialog.
            :type parent: MainWindow
            :param animatedGraphManager: The manager that holds all of the graphed data to be exported.
            :type animatedGraphManager: AnimatedGraphManager
            :param startStreamUnixTime: The estimated time when the stream was started using seconds from the Unix epoch.
            :type startStreamUnixTime: float
            :param controlLogicEnumType: The Enum type that facilitates the state of which control logic was used. Used in converting values.
            :type controlLogicEnumType: type
        """
        super().__init__(parent)
        # Run the .setupUi() method to show the GUI
        self.setupUi(self)

        self.animatedGraphManager = animatedGraphManager
        self.saveDialogButtonBox.accepted.connect(partial(SaveDialog.saveStreamedData, parent, self.animatedGraphManager, startStreamUnixTime, controlLogicEnumType)) # Pressing "No" just leaves the dialog box.

    @staticmethod
    def exporterFactory(suffix: str) -> AbstractDataExporter:
        """
            Gets the exporter based on the suffix of the file.

            :param suffix: The file extension to be used for the file.
            :type suffix: str
            :return: The exporter that should be used for the graphed data.
            :rtype: AbstractDataExporter
        """
        if suffix == '.parquet':
            exporter = ParquetExporter()
        elif suffix in {'.hdf5', '.h5'}: 
            exporter = HDF5Exporter()
        return exporter
    
    @Slot()
    @staticmethod
    def saveStreamedData(parent: MainWindow, animatedGraphManager: AnimatedGraphManager, startStreamUnixTime: float, controlLogicEnumType: type) -> None:
        """
            Saves the stream data, getting the experiment numbers and formatting the time in the filename.
            Trial numbers are incremented after a successful save for convenience.

            :param parent: The parent saving GUI that runs this dialog.
            :type parent: MainWindow
            :param animatedGraphManager: The manager that holds all of the graphed data to be exported.
            :type animatedGraphManager: AnimatedGraphManager
            :param startStreamUnixTime: The estimated time when the stream was started using seconds from the Unix epoch.
            :type startStreamUnixTime: float
            :param controlLogicEnumType: The Enum type that facilitates the state of which control logic was used. Used in converting values.
            :type controlLogicEnumType: type
        """
        ubqNumber, visitNumber, trialNumber = parent.ubqExperimentGroup.getNumbers()
        options = QFileDialog.Option() # Must use DontUseNativeDialog for other options to work.
        fileDialog = QFileDialog(parent)
        creationTime = datetime.now().strftime(f'UBQ{ubqNumber:02}_v{visitNumber:02}_t{trialNumber:02}_%Y%m%d_%H%M%S')
        fileName, fileFormat = fileDialog.getSaveFileName(parent, "Save As", creationTime, 
                                                          "Parquet Files (*.parquet);;HDF5 Files (*.h5)", options = options)
        
        if fileName:
            fileNameSuffix = pathlib.Path(fileName).suffix

            # Assume that all of the file formats have the ')' at the end.
            fileFormatWithoutRightParenthesis = fileFormat.removesuffix(")")
            fileFormatSuffix = pathlib.Path(fileFormatWithoutRightParenthesis).suffix

            # Prefer the fileNameSuffix to the fileFormatSuffix to determine which file export to use.
            # This ensures that the person gets the file format that they explicitly wanted.
            if fileNameSuffix in {'.parquet', '.h5'}:
                filePath = fileName
                suffixToUse = fileNameSuffix
            else:
                # In the case where it's not a supported file format (e.g. user added .pdf to the end)
                # just take the full filename and append the suffix from the fileFormatSuffix.

                filePath = pathlib.Path(fileName).with_suffix(fileNameSuffix + fileFormatSuffix)
                suffixToUse = fileFormatSuffix
                logger.info(f"Invalid file format, adjusted to {filePath}") 
            
            exporter = SaveDialog.exporterFactory(suffixToUse)
            exporter.exportData(animatedGraphManager, filePath, startStreamUnixTime, controlLogicEnumType, parent)
            parent.ubqExperimentGroup.trialSpinBox.setValue(parent.ubqExperimentGroup.trialSpinBox.value() + 1) # Auto-increment on successful save.