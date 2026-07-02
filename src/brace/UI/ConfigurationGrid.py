from PySide6.QtWidgets import QWidget
from pathlib import Path
import numpy as np

import logging
logger = logging.getLogger("logger")

from brace.UI.view.ui.components.Ui_ConfigurationGrid import Ui_ConfigurationGrid
import sys
from pathlib import Path
parent_dir = str(Path(__file__).resolve().parent)
sys.path.append(parent_dir)

class ConfigurationGrid(QWidget, Ui_ConfigurationGrid):
    """
        This widget is the Configuration box that contains all of the
        fields that may be used in changing parameters in the remote.
        It is also used in the simulator, with one constant set on the top
        and another mutable set on the bottom. 
    """
    def __init__(self, parent = None):
        super().__init__(parent)
        self.setupUi(self)