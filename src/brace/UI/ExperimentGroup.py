from PySide6.QtWidgets import QWidget
import logging
logger = logging.getLogger("logger")

from brace.UI.view.ui.components.Ui_ExperimentGroup import Ui_UBQVisitTrials
import sys
from pathlib import Path
parent_dir = str(Path(__file__).resolve().parent)
sys.path.append(parent_dir)

class ExperimentGroup(QWidget, Ui_UBQVisitTrials):
    """
        This widget is found on the right of the calibrate button.
        Sets subject, visit, and trial numbers that are used in the filenames of saved files.
    """
    def __init__(self, parent = None):
        super().__init__(parent)
        self.setupUi(self)

    def getNumbers(self) -> tuple[int, int, int]:
        return (self.ubqSpinBox.value(), self.visitSpinBox.value(), self.trialSpinBox.value())