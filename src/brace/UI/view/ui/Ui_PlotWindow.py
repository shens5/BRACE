# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'openPlotWindowEGMaxC.ui'
##
## Created by: Qt User Interface Compiler version 6.9.0
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QAction, QBrush, QColor, QConicalGradient,
    QCursor, QFont, QFontDatabase, QGradient,
    QIcon, QImage, QKeySequence, QLinearGradient,
    QPainter, QPalette, QPixmap, QRadialGradient,
    QTransform)
from PySide6.QtWidgets import (QApplication, QGridLayout, QMainWindow, QMenu,
    QMenuBar, QSizePolicy, QStatusBar, QTabWidget,
    QWidget)

class Ui_PlotWindow(object):
    def setupUi(self, PlotWindow):
        if not PlotWindow.objectName():
            PlotWindow.setObjectName(u"PlotWindow")
        PlotWindow.resize(1600, 900)
        font = QFont()
        font.setPointSize(9)
        PlotWindow.setFont(font)
        self.actionExit = QAction(PlotWindow)
        self.actionExit.setObjectName(u"actionExit")
        icon = QIcon(QIcon.fromTheme(QIcon.ThemeIcon.WindowClose))
        self.actionExit.setIcon(icon)
        self.centralwidget = QWidget(PlotWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.gridLayout = QGridLayout(self.centralwidget)
        self.gridLayout.setObjectName(u"gridLayout")
        self.plotTabWidget = QTabWidget(self.centralwidget)
        self.plotTabWidget.setObjectName(u"plotTabWidget")
        self.plotTabWidget.setTabsClosable(False)
        self.plotTabWidget.setMovable(True)

        self.gridLayout.addWidget(self.plotTabWidget, 0, 0, 1, 1)

        PlotWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(PlotWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 1600, 33))
        self.menuFile = QMenu(self.menubar)
        self.menuFile.setObjectName(u"menuFile")
        PlotWindow.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(PlotWindow)
        self.statusbar.setObjectName(u"statusbar")
        PlotWindow.setStatusBar(self.statusbar)

        self.menubar.addAction(self.menuFile.menuAction())
        self.menuFile.addAction(self.actionExit)

        self.retranslateUi(PlotWindow)
        self.actionExit.triggered.connect(PlotWindow.close)

        self.plotTabWidget.setCurrentIndex(-1)


        QMetaObject.connectSlotsByName(PlotWindow)
    # setupUi

    def retranslateUi(self, PlotWindow):
        PlotWindow.setWindowTitle(QCoreApplication.translate("PlotWindow", u"Data Plot", None))
        self.actionExit.setText(QCoreApplication.translate("PlotWindow", u"Exit", None))
        self.menuFile.setTitle(QCoreApplication.translate("PlotWindow", u"File", None))
    # retranslateUi

