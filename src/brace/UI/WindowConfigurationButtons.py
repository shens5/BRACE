from PySide6.QtWidgets import QWidget

import logging
logger = logging.getLogger("logger")

from brace.UI.view.ui.components.Ui_WindowConfigurationButtons import Ui_ConfigurationButtons
import sys
from pathlib import Path
parent_dir = str(Path(__file__).resolve().parent)
sys.path.append(parent_dir)

class WindowConfigurationButtons(QWidget, Ui_ConfigurationButtons):
    """
        These are the configuration buttons that are in the main GUI
        that are found below the configuration box.
    """
    def __init__(self, parent = None):
        super().__init__(parent)
        self.setupUi(self)

    def toggleDisabledConfigurationWidgets(self, disabled: bool) -> None:
        self.readConfigurationButton.setDisabled(disabled)
        self.writeChangesButton.setDisabled(disabled)
        self.loadConfigurationFromFileButton.setDisabled(disabled)
        self.saveConfigurationToFileButton.setDisabled(disabled)
        self.readAllConfigurationButton.setDisabled(disabled)
        self.writeAllChangesButton.setDisabled(disabled)