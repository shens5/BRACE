# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'simulatorAlhGIh.ui'
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
    QMenuBar, QSizePolicy, QStatusBar, QWidget)

from brace.UI.ConfigurationGrid import ConfigurationGrid
from brace.UI.PlotsPage import PlotsPage
from brace.UI.SimulatorConfigurationButtons import SimulatorConfigurationButtons

class Ui_Simulator(object):
    def setupUi(self, Simulator):
        if not Simulator.objectName():
            Simulator.setObjectName(u"Simulator")
        Simulator.resize(1440, 720)
        self.actionExit = QAction(Simulator)
        self.actionExit.setObjectName(u"actionExit")
        icon = QIcon(QIcon.fromTheme(QIcon.ThemeIcon.ApplicationExit))
        self.actionExit.setIcon(icon)
        self.actionLightMode = QAction(Simulator)
        self.actionLightMode.setObjectName(u"actionLightMode")
        self.actionLightMode.setCheckable(True)
        self.actionDarkMode = QAction(Simulator)
        self.actionDarkMode.setObjectName(u"actionDarkMode")
        self.actionDarkMode.setCheckable(True)
        self.actionSystemDefault = QAction(Simulator)
        self.actionSystemDefault.setObjectName(u"actionSystemDefault")
        self.actionSystemDefault.setCheckable(True)
        self.actionSystemDefault.setChecked(True)
        self.centralwidget = QWidget(Simulator)
        self.centralwidget.setObjectName(u"centralwidget")
        self.centralWidgetGridLayout = QGridLayout(self.centralwidget)
        self.centralWidgetGridLayout.setObjectName(u"centralWidgetGridLayout")
        self.centralWidgetGridLayout.setContentsMargins(-1, -1, -1, 9)
        self.configurationGridLayout = QGridLayout()
        self.configurationGridLayout.setSpacing(0)
        self.configurationGridLayout.setObjectName(u"configurationGridLayout")
        self.configurationButtons = SimulatorConfigurationButtons(self.centralwidget)
        self.configurationButtons.setObjectName(u"configurationButtons")

        self.configurationGridLayout.addWidget(self.configurationButtons, 2, 0, 1, 1)

        self.configurationGridNew = ConfigurationGrid(self.centralwidget)
        self.configurationGridNew.setObjectName(u"configurationGridNew")

        self.configurationGridLayout.addWidget(self.configurationGridNew, 1, 0, 1, 1)

        self.configurationGridOld = ConfigurationGrid(self.centralwidget)
        self.configurationGridOld.setObjectName(u"configurationGridOld")

        self.configurationGridLayout.addWidget(self.configurationGridOld, 0, 0, 1, 1)


        self.centralWidgetGridLayout.addLayout(self.configurationGridLayout, 0, 1, 1, 1)

        self.plotsPage = PlotsPage(self.centralwidget)
        self.plotsPage.setObjectName(u"plotsPage")

        self.centralWidgetGridLayout.addWidget(self.plotsPage, 0, 0, 1, 1)

        self.centralWidgetGridLayout.setColumnStretch(0, 5)
        self.centralWidgetGridLayout.setColumnStretch(1, 1)
        Simulator.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(Simulator)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 1440, 33))
        self.menuFile = QMenu(self.menubar)
        self.menuFile.setObjectName(u"menuFile")
        self.menuOptions = QMenu(self.menubar)
        self.menuOptions.setObjectName(u"menuOptions")
        self.menuColors = QMenu(self.menuOptions)
        self.menuColors.setObjectName(u"menuColors")
        Simulator.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(Simulator)
        self.statusbar.setObjectName(u"statusbar")
        Simulator.setStatusBar(self.statusbar)

        self.menubar.addAction(self.menuFile.menuAction())
        self.menubar.addAction(self.menuOptions.menuAction())
        self.menuFile.addAction(self.actionExit)
        self.menuOptions.addAction(self.menuColors.menuAction())
        self.menuColors.addAction(self.actionLightMode)
        self.menuColors.addAction(self.actionDarkMode)
        self.menuColors.addAction(self.actionSystemDefault)

        self.retranslateUi(Simulator)
        self.actionExit.triggered.connect(Simulator.close)

        QMetaObject.connectSlotsByName(Simulator)
    # setupUi

    def retranslateUi(self, Simulator):
        Simulator.setWindowTitle(QCoreApplication.translate("Simulator", u"Simulator", None))
        self.actionExit.setText(QCoreApplication.translate("Simulator", u"Exit", None))
        self.actionLightMode.setText(QCoreApplication.translate("Simulator", u"Light Mode", None))
        self.actionDarkMode.setText(QCoreApplication.translate("Simulator", u"Dark Mode", None))
        self.actionSystemDefault.setText(QCoreApplication.translate("Simulator", u"System Default", None))
        self.menuFile.setTitle(QCoreApplication.translate("Simulator", u"File", None))
        self.menuOptions.setTitle(QCoreApplication.translate("Simulator", u"Options", None))
        self.menuColors.setTitle(QCoreApplication.translate("Simulator", u"Colors", None))
    # retranslateUi

