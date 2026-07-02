from PySide6.QtWidgets import QWidget
import logging
logger = logging.getLogger("logger")

from brace.UI.view.ui.Ui_PlotTabs import Ui_PlotsPage
import sys
from pathlib import Path
parent_dir = str(Path(__file__).resolve().parent)
sys.path.append(parent_dir)

class PlotsPage(QWidget, Ui_PlotsPage):
    """
        The box on the GUI that contains the plots in separate tabs.
    """
    def __init__(self, parent = None):
        super().__init__(parent)
        self.setupUi(self)