import atexit
from datetime import datetime
import logging
import os
import sys
from PySide6.QtWidgets import QApplication
from brace.UI.LoggingHelpers import TextBrowserHandler
from brace.example.zaber.MainWindow import ZaberMainWindow

# Handles uncaught exceptions.
def handleException(excType, excValue, excTraceback):
    if issubclass(excType, KeyboardInterrupt):
        sys.__excepthook__(excType, excValue, excTraceback)
        return

    logger.error("Uncaught exception", exc_info = (excType, excValue, excTraceback))

def main():
    logger.setLevel(logging.DEBUG)  # Logger debug has to be set to the "lowest" level
    formatter = logging.Formatter(fmt = '%(asctime)s.%(msecs)03d %(levelname)s: %(message)s', 
                                  datefmt = '%Y-%m-%d %H:%M:%S')

    # Log handler for the text browser
    textBrowserHandler = TextBrowserHandler()
    textBrowserHandler.setLevel(logging.INFO)
    textBrowserHandler.setFormatter(formatter)
    logger.addHandler(textBrowserHandler)

    # Log handler for the standard output.
    streamHandler = logging.StreamHandler(sys.stdout) 
    streamHandler.setLevel(logging.DEBUG)
    streamHandler.setFormatter(formatter)
    logger.addHandler(streamHandler)

    fileFormatter = logging.Formatter(fmt = '%(asctime)s.%(msecs)03d %(levelname)s, [%(pathname)s, %(filename)s, %(module)s, %(funcName)s, %(lineno)d]: %(message)s', 
                                  datefmt = '%Y-%m-%d %H:%M:%S')
    dirPath = os.path.dirname(os.path.realpath(__file__))   
    logsPath = os.path.join(dirPath, 'logs')
    os.makedirs(logsPath, exist_ok = True)
    logFileName = os.path.join(logsPath, datetime.now().strftime('%Y%m%d_%H%M%S_GUI.log'))
    fileHandler = logging.FileHandler(logFileName)
    fileHandler.setLevel(logging.DEBUG)
    fileHandler.setFormatter(fileFormatter)
    logger.addHandler(fileHandler)

    sys.excepthook = handleException
    
    atexit.register(lambda: logger.debug(f"Session ended at {datetime.now().strftime("%Y/%m/%d %H:%M:%S.%f")}"))

    app = QApplication(sys.argv)
    mainWindow = ZaberMainWindow(app, textBrowserHandler)
    mainWindow.showMaximized()
    mainWindow.show()
    sys.exit(app.exec())
    
if __name__ == '__main__':
    logger = logging.getLogger('logger')
    main()