from PySide6 import QtWidgets
import logging
from multiprocessing import RLock

def joinStringsWithSpace(*argv) -> str:
    return " ".join(argv)

def redBoldText(stringToBold: str) -> str:
    """
        Formats the text to be red and bold when displayed out to the textbox.
        
        :param stringToBold: The string that should be displayed as bold.
        :type stringToBold: str
        :return: A bolded and red string using tags.
        :rtype: str
    """
    return f"<b style=\"color:red;\">{stringToBold}</b>"

class TextBrowserHandler(logging.Handler):
    RED_WARN = "RED_WARN"
    textBrowser: QtWidgets.QTextBrowser
    lock = RLock()

    def emit(self, record):
        """
            Emits out the record onto the textbox. If the record
            is given a RED_WARN, then the text will be bolded.
        """
        with self.lock as _:
            if record.__dict__.get(TextBrowserHandler.RED_WARN, False):
                self.textBrowser.append(redBoldText(self.format(record)))
            else:
                self.textBrowser.append(self.format(record))