from typing import Generator
from PySide6 import QtWidgets
from PySide6.QtWidgets import QApplication, QFileDialog, QWidget
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
import pandas as pd
from pathlib import Path
from pyqtgraph import QtCore
import numpy as np

import logging
logger = logging.getLogger("logger")

from brace.UI.view.ui.components.Ui_SimulatorConfigurationButtons import Ui_ConfigurationButtons
import sys
from pathlib import Path
parent_dir = str(Path(__file__).resolve().parent)
sys.path.append(parent_dir)

class SimulatorConfigurationButtons(QWidget, Ui_ConfigurationButtons):
    """
        These are the configuration buttons used in the simulator underneath the
        configuration box.
    """
    def __init__(self, parent = None):
        super().__init__(parent)
        self.setupUi(self)

    def toggleConfigurationButtons(self, enable: bool) -> None:
        self.simulatePushButton.setEnabled(enable)
        self.resetCurrentConfigurationPushButton.setEnabled(enable)
        self.resetAllConfigurationPushButton.setEnabled(enable)
        self.saveCurrentConfigurationPushButton.setEnabled(enable)