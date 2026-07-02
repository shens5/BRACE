# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'mainwindowDOwVRL.ui'
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
from PySide6.QtWidgets import (QAbstractScrollArea, QApplication, QComboBox, QFormLayout,
    QFrame, QGridLayout, QGroupBox, QHBoxLayout,
    QLabel, QMainWindow, QMenu, QMenuBar,
    QPushButton, QSizePolicy, QTextBrowser, QTextEdit,
    QVBoxLayout, QWidget)

from brace.UI.ConfigurationGrid import ConfigurationGrid
from brace.UI.ExperimentGroup import ExperimentGroup
from brace.UI.PlotsPage import PlotsPage
from brace.UI.WindowConfigurationButtons import WindowConfigurationButtons

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(2120, 909)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(MainWindow.sizePolicy().hasHeightForWidth())
        MainWindow.setSizePolicy(sizePolicy)
        MainWindow.setWindowTitle(u"MainWindow - Play Around with this")
#if QT_CONFIG(tooltip)
        MainWindow.setToolTip(u"")
#endif // QT_CONFIG(tooltip)
        self.actionSaveData = QAction(MainWindow)
        self.actionSaveData.setObjectName(u"actionSaveData")
        icon = QIcon(QIcon.fromTheme(QIcon.ThemeIcon.DocumentSaveAs))
        self.actionSaveData.setIcon(icon)
        font = QFont()
        self.actionSaveData.setFont(font)
        self.actionExit = QAction(MainWindow)
        self.actionExit.setObjectName(u"actionExit")
        icon1 = QIcon(QIcon.fromTheme(QIcon.ThemeIcon.ApplicationExit))
        self.actionExit.setIcon(icon1)
        self.actionExit.setText(u"Exit")
        self.actionExit.setFont(font)
        self.actionLightMode = QAction(MainWindow)
        self.actionLightMode.setObjectName(u"actionLightMode")
        self.actionLightMode.setCheckable(True)
        self.actionLightMode.setChecked(False)
        self.actionLightMode.setText(u"Light Mode")
        self.actionLightMode.setFont(font)
        self.actionDarkMode = QAction(MainWindow)
        self.actionDarkMode.setObjectName(u"actionDarkMode")
        self.actionDarkMode.setCheckable(True)
        self.actionDarkMode.setText(u"Dark Mode")
        self.actionDarkMode.setFont(font)
        self.actionSystemDefault = QAction(MainWindow)
        self.actionSystemDefault.setObjectName(u"actionSystemDefault")
        self.actionSystemDefault.setCheckable(True)
        self.actionSystemDefault.setChecked(True)
        self.actionSystemDefault.setText(u"System Default")
        self.actionSystemDefault.setFont(font)
        self.actionOpenData = QAction(MainWindow)
        self.actionOpenData.setObjectName(u"actionOpenData")
        icon2 = QIcon(QIcon.fromTheme(QIcon.ThemeIcon.DocumentOpen))
        self.actionOpenData.setIcon(icon2)
        self.actionOpenData.setFont(font)
        self.actionOpenSimulator = QAction(MainWindow)
        self.actionOpenSimulator.setObjectName(u"actionOpenSimulator")
        icon3 = QIcon(QIcon.fromTheme(QIcon.ThemeIcon.AppointmentNew))
        self.actionOpenSimulator.setIcon(icon3)
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        sizePolicy.setHeightForWidth(self.centralwidget.sizePolicy().hasHeightForWidth())
        self.centralwidget.setSizePolicy(sizePolicy)
        self.centralWidgetGridLayout = QGridLayout(self.centralwidget)
        self.centralWidgetGridLayout.setSpacing(0)
        self.centralWidgetGridLayout.setObjectName(u"centralWidgetGridLayout")
        self.centralWidgetGridLayout.setContentsMargins(0, 0, 0, 0)
        self.connectionCalibrationExperimentGridLayout = QGridLayout()
        self.connectionCalibrationExperimentGridLayout.setObjectName(u"connectionCalibrationExperimentGridLayout")
        self.connectGroupBox = QGroupBox(self.centralwidget)
        self.connectGroupBox.setObjectName(u"connectGroupBox")
        sizePolicy.setHeightForWidth(self.connectGroupBox.sizePolicy().hasHeightForWidth())
        self.connectGroupBox.setSizePolicy(sizePolicy)
        self.connectGroupBox.setMinimumSize(QSize(0, 0))
        font1 = QFont()
        font1.setPointSize(9)
        self.connectGroupBox.setFont(font1)
        self.connectGroupBox.setTitle(u"Connect")
        self.connectGroupBoxVerticalLayout = QVBoxLayout(self.connectGroupBox)
        self.connectGroupBoxVerticalLayout.setSpacing(3)
        self.connectGroupBoxVerticalLayout.setObjectName(u"connectGroupBoxVerticalLayout")
        self.connectGroupBoxVerticalLayout.setContentsMargins(-1, 6, -1, 6)
        self.connectToRaspberryPiButton = QPushButton(self.connectGroupBox)
        self.connectToRaspberryPiButton.setObjectName(u"connectToRaspberryPiButton")
        sizePolicy.setHeightForWidth(self.connectToRaspberryPiButton.sizePolicy().hasHeightForWidth())
        self.connectToRaspberryPiButton.setSizePolicy(sizePolicy)
        font2 = QFont()
        font2.setPointSize(11)
        self.connectToRaspberryPiButton.setFont(font2)
        self.connectToRaspberryPiButton.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.connectToRaspberryPiButton.setText(u"Connect to Raspberry Pi")

        self.connectGroupBoxVerticalLayout.addWidget(self.connectToRaspberryPiButton)


        self.connectionCalibrationExperimentGridLayout.addWidget(self.connectGroupBox, 0, 0, 1, 1)

        self.ubqExperimentGroup = ExperimentGroup(self.centralwidget)
        self.ubqExperimentGroup.setObjectName(u"ubqExperimentGroup")

        self.connectionCalibrationExperimentGridLayout.addWidget(self.ubqExperimentGroup, 0, 1, 2, 1)

        self.calibrationGroupBox = QGroupBox(self.centralwidget)
        self.calibrationGroupBox.setObjectName(u"calibrationGroupBox")
        sizePolicy.setHeightForWidth(self.calibrationGroupBox.sizePolicy().hasHeightForWidth())
        self.calibrationGroupBox.setSizePolicy(sizePolicy)
        self.calibrationGroupBox.setMinimumSize(QSize(0, 0))
        self.calibrationGroupBox.setFont(font1)
        self.calibrationGroupBox.setTitle(u"Calibration")
        self.calibrationGroupBoxVerticalLayout = QVBoxLayout(self.calibrationGroupBox)
        self.calibrationGroupBoxVerticalLayout.setSpacing(3)
        self.calibrationGroupBoxVerticalLayout.setObjectName(u"calibrationGroupBoxVerticalLayout")
        self.calibrationGroupBoxVerticalLayout.setContentsMargins(-1, 6, -1, 6)
        self.setCalibrationButton = QPushButton(self.calibrationGroupBox)
        self.setCalibrationButton.setObjectName(u"setCalibrationButton")
        sizePolicy.setHeightForWidth(self.setCalibrationButton.sizePolicy().hasHeightForWidth())
        self.setCalibrationButton.setSizePolicy(sizePolicy)
        self.setCalibrationButton.setFont(font2)
        self.setCalibrationButton.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setCalibrationButton.setText(u"Set Full Knee Extension")

        self.calibrationGroupBoxVerticalLayout.addWidget(self.setCalibrationButton)


        self.connectionCalibrationExperimentGridLayout.addWidget(self.calibrationGroupBox, 1, 0, 1, 1)

        self.connectionCalibrationExperimentGridLayout.setRowStretch(0, 1)
        self.connectionCalibrationExperimentGridLayout.setRowStretch(1, 1)
        self.connectionCalibrationExperimentGridLayout.setColumnStretch(0, 4)
        self.connectionCalibrationExperimentGridLayout.setColumnStretch(1, 1)

        self.centralWidgetGridLayout.addLayout(self.connectionCalibrationExperimentGridLayout, 0, 0, 1, 1)

        self.plotTabWidget = PlotsPage(self.centralwidget)
        self.plotTabWidget.setObjectName(u"plotTabWidget")

        self.centralWidgetGridLayout.addWidget(self.plotTabWidget, 0, 1, 5, 1)

        self.configurationBox = ConfigurationGrid(self.centralwidget)
        self.configurationBox.setObjectName(u"configurationBox")
        sizePolicy.setHeightForWidth(self.configurationBox.sizePolicy().hasHeightForWidth())
        self.configurationBox.setSizePolicy(sizePolicy)
        self.configurationBox.setFont(font1)

        self.centralWidgetGridLayout.addWidget(self.configurationBox, 1, 0, 1, 1)

        self.windowConfigurationButtons = WindowConfigurationButtons(self.centralwidget)
        self.windowConfigurationButtons.setObjectName(u"windowConfigurationButtons")

        self.centralWidgetGridLayout.addWidget(self.windowConfigurationButtons, 2, 0, 1, 1)

        self.legSessionHorizontalLayout = QHBoxLayout()
        self.legSessionHorizontalLayout.setObjectName(u"legSessionHorizontalLayout")
        self.sessionGroupBox = QGroupBox(self.centralwidget)
        self.sessionGroupBox.setObjectName(u"sessionGroupBox")
        sizePolicy.setHeightForWidth(self.sessionGroupBox.sizePolicy().hasHeightForWidth())
        self.sessionGroupBox.setSizePolicy(sizePolicy)
        font3 = QFont()
        font3.setPointSize(9)
        font3.setBold(False)
        self.sessionGroupBox.setFont(font3)
        self.sessionGroupBox.setTitle(u"Session")
        self.sessionGroupVerticalLayout = QVBoxLayout(self.sessionGroupBox)
        self.sessionGroupVerticalLayout.setSpacing(3)
        self.sessionGroupVerticalLayout.setObjectName(u"sessionGroupVerticalLayout")
        self.sessionGroupVerticalLayout.setContentsMargins(-1, 6, -1, 6)
        self.enableTorqueButton = QPushButton(self.sessionGroupBox)
        self.enableTorqueButton.setObjectName(u"enableTorqueButton")
        sizePolicy.setHeightForWidth(self.enableTorqueButton.sizePolicy().hasHeightForWidth())
        self.enableTorqueButton.setSizePolicy(sizePolicy)
        self.enableTorqueButton.setFont(font3)
        self.enableTorqueButton.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.enableTorqueButton.setText(u"Enable Torque")
        self.enableTorqueButton.setCheckable(True)

        self.sessionGroupVerticalLayout.addWidget(self.enableTorqueButton)

        self.startStreamPushButton = QPushButton(self.sessionGroupBox)
        self.startStreamPushButton.setObjectName(u"startStreamPushButton")
        sizePolicy.setHeightForWidth(self.startStreamPushButton.sizePolicy().hasHeightForWidth())
        self.startStreamPushButton.setSizePolicy(sizePolicy)
        self.startStreamPushButton.setFont(font3)
        self.startStreamPushButton.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.startStreamPushButton.setText(u"Start Stream")
        self.startStreamPushButton.setCheckable(True)
        self.startStreamPushButton.setAutoDefault(True)

        self.sessionGroupVerticalLayout.addWidget(self.startStreamPushButton)


        self.legSessionHorizontalLayout.addWidget(self.sessionGroupBox)

        self.legUsedGroupBox = QGroupBox(self.centralwidget)
        self.legUsedGroupBox.setObjectName(u"legUsedGroupBox")
        sizePolicy.setHeightForWidth(self.legUsedGroupBox.sizePolicy().hasHeightForWidth())
        self.legUsedGroupBox.setSizePolicy(sizePolicy)
        self.legUsedGroupBox.setFont(font1)
        self.legUsedFormLayout = QFormLayout(self.legUsedGroupBox)
        self.legUsedFormLayout.setObjectName(u"legUsedFormLayout")
        self.legUsedFormLayout.setVerticalSpacing(12)
        self.legUsedFormLayout.setContentsMargins(-1, 6, -1, 6)
        self.legLabelL = QLabel(self.legUsedGroupBox)
        self.legLabelL.setObjectName(u"legLabelL")
        sizePolicy.setHeightForWidth(self.legLabelL.sizePolicy().hasHeightForWidth())
        self.legLabelL.setSizePolicy(sizePolicy)
        self.legLabelL.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)

        self.legUsedFormLayout.setWidget(0, QFormLayout.ItemRole.LabelRole, self.legLabelL)

        self.legComboBoxL = QComboBox(self.legUsedGroupBox)
        self.legComboBoxL.addItem("")
        self.legComboBoxL.setObjectName(u"legComboBoxL")
        sizePolicy.setHeightForWidth(self.legComboBoxL.sizePolicy().hasHeightForWidth())
        self.legComboBoxL.setSizePolicy(sizePolicy)
        self.legComboBoxL.setFont(font1)
        self.legComboBoxL.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        self.legUsedFormLayout.setWidget(0, QFormLayout.ItemRole.FieldRole, self.legComboBoxL)

        self.legComboBoxR = QComboBox(self.legUsedGroupBox)
        self.legComboBoxR.addItem("")
        self.legComboBoxR.setObjectName(u"legComboBoxR")
        sizePolicy.setHeightForWidth(self.legComboBoxR.sizePolicy().hasHeightForWidth())
        self.legComboBoxR.setSizePolicy(sizePolicy)
        self.legComboBoxR.setFont(font1)
        self.legComboBoxR.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        self.legUsedFormLayout.setWidget(1, QFormLayout.ItemRole.FieldRole, self.legComboBoxR)

        self.legLabelR = QLabel(self.legUsedGroupBox)
        self.legLabelR.setObjectName(u"legLabelR")
        sizePolicy.setHeightForWidth(self.legLabelR.sizePolicy().hasHeightForWidth())
        self.legLabelR.setSizePolicy(sizePolicy)
        self.legLabelR.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)

        self.legUsedFormLayout.setWidget(1, QFormLayout.ItemRole.LabelRole, self.legLabelR)


        self.legSessionHorizontalLayout.addWidget(self.legUsedGroupBox)


        self.centralWidgetGridLayout.addLayout(self.legSessionHorizontalLayout, 3, 0, 1, 1)

        self.statusGroupBox = QGroupBox(self.centralwidget)
        self.statusGroupBox.setObjectName(u"statusGroupBox")
        sizePolicy.setHeightForWidth(self.statusGroupBox.sizePolicy().hasHeightForWidth())
        self.statusGroupBox.setSizePolicy(sizePolicy)
        self.statusGroupBox.setMinimumSize(QSize(0, 0))
        self.statusGroupBox.setFont(font1)
        self.statusGroupBox.setCursor(QCursor(Qt.CursorShape.IBeamCursor))
        self.statusGroupBox.setTitle(u"Status")
        self.statusGroupBoxVerticalLayout = QVBoxLayout(self.statusGroupBox)
        self.statusGroupBoxVerticalLayout.setObjectName(u"statusGroupBoxVerticalLayout")
        self.statusTextBrowser = QTextBrowser(self.statusGroupBox)
        self.statusTextBrowser.setObjectName(u"statusTextBrowser")
        sizePolicy.setHeightForWidth(self.statusTextBrowser.sizePolicy().hasHeightForWidth())
        self.statusTextBrowser.setSizePolicy(sizePolicy)
        self.statusTextBrowser.viewport().setProperty(u"cursor", QCursor(Qt.CursorShape.IBeamCursor))
        self.statusTextBrowser.setFrameShape(QFrame.Shape.StyledPanel)
        self.statusTextBrowser.setFrameShadow(QFrame.Shadow.Sunken)
        self.statusTextBrowser.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.statusTextBrowser.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.statusTextBrowser.setSizeAdjustPolicy(QAbstractScrollArea.SizeAdjustPolicy.AdjustToContents)
        self.statusTextBrowser.setTabChangesFocus(True)
        self.statusTextBrowser.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        self.statusTextBrowser.setHtml(u"<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><meta charset=\"utf-8\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"hr { height: 1px; border-width: 0; }\n"
"li.unchecked::marker { content: \"\\2610\"; }\n"
"li.checked::marker { content: \"\\2612\"; }\n"
"</style></head><body style=\" font-family:'Segoe UI'; font-size:9pt; font-weight:400; font-style:normal;\">\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:10pt;\"><br /></p></body></html>")
        self.statusTextBrowser.setTextInteractionFlags(Qt.TextInteractionFlag.LinksAccessibleByKeyboard|Qt.TextInteractionFlag.LinksAccessibleByMouse|Qt.TextInteractionFlag.TextBrowserInteraction|Qt.TextInteractionFlag.TextSelectableByKeyboard|Qt.TextInteractionFlag.TextSelectableByMouse)

        self.statusGroupBoxVerticalLayout.addWidget(self.statusTextBrowser)


        self.centralWidgetGridLayout.addWidget(self.statusGroupBox, 4, 0, 1, 1)

        self.centralWidgetGridLayout.setRowStretch(0, 1)
        self.centralWidgetGridLayout.setRowStretch(1, 5)
        self.centralWidgetGridLayout.setRowStretch(2, 1)
        self.centralWidgetGridLayout.setRowStretch(3, 1)
        self.centralWidgetGridLayout.setRowStretch(4, 3)
        self.centralWidgetGridLayout.setColumnStretch(0, 1)
        self.centralWidgetGridLayout.setColumnStretch(1, 2)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 2120, 33))
        self.menubar.setFont(font1)
        self.menuMenu = QMenu(self.menubar)
        self.menuMenu.setObjectName(u"menuMenu")
        self.menuMenu.setFont(font1)
        self.menuMenu.setTitle(u"File")
        self.menuOptions = QMenu(self.menubar)
        self.menuOptions.setObjectName(u"menuOptions")
        self.menuOptions.setFont(font1)
        self.menuOptions.setTitle(u"Options")
        self.menuColors = QMenu(self.menuOptions)
        self.menuColors.setObjectName(u"menuColors")
        self.menuColors.setFont(font1)
        self.menuColors.setTitle(u"Colors")
        MainWindow.setMenuBar(self.menubar)
        QWidget.setTabOrder(self.connectToRaspberryPiButton, self.setCalibrationButton)
        QWidget.setTabOrder(self.setCalibrationButton, self.enableTorqueButton)
        QWidget.setTabOrder(self.enableTorqueButton, self.startStreamPushButton)
        QWidget.setTabOrder(self.startStreamPushButton, self.legComboBoxL)
        QWidget.setTabOrder(self.legComboBoxL, self.legComboBoxR)
        QWidget.setTabOrder(self.legComboBoxR, self.statusTextBrowser)

        self.menubar.addAction(self.menuMenu.menuAction())
        self.menubar.addAction(self.menuOptions.menuAction())
        self.menuMenu.addAction(self.actionOpenData)
        self.menuMenu.addAction(self.actionSaveData)
        self.menuMenu.addSeparator()
        self.menuMenu.addAction(self.actionOpenSimulator)
        self.menuMenu.addSeparator()
        self.menuMenu.addAction(self.actionExit)
        self.menuOptions.addAction(self.menuColors.menuAction())
        self.menuColors.addAction(self.actionLightMode)
        self.menuColors.addAction(self.actionDarkMode)
        self.menuColors.addAction(self.actionSystemDefault)

        self.retranslateUi(MainWindow)
        self.actionExit.triggered.connect(MainWindow.close)

        self.startStreamPushButton.setDefault(True)


        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        self.actionSaveData.setText(QCoreApplication.translate("MainWindow", u"Save Data As...", None))
        self.actionSaveData.setIconText(QCoreApplication.translate("MainWindow", u"Save As", None))
#if QT_CONFIG(shortcut)
        self.actionSaveData.setShortcut(QCoreApplication.translate("MainWindow", u"Ctrl+S", None))
#endif // QT_CONFIG(shortcut)
        self.actionOpenData.setText(QCoreApplication.translate("MainWindow", u"Open Data", None))
#if QT_CONFIG(shortcut)
        self.actionOpenData.setShortcut(QCoreApplication.translate("MainWindow", u"Ctrl+O", None))
#endif // QT_CONFIG(shortcut)
        self.actionOpenSimulator.setText(QCoreApplication.translate("MainWindow", u"Open Simulator", None))
        self.legUsedGroupBox.setTitle(QCoreApplication.translate("MainWindow", u"Leg Used", None))
        self.legLabelL.setText(QCoreApplication.translate("MainWindow", u"Left Leg", None))
        self.legComboBoxL.setItemText(0, QCoreApplication.translate("MainWindow", u"None", None))

        self.legComboBoxR.setItemText(0, QCoreApplication.translate("MainWindow", u"None", None))

        self.legLabelR.setText(QCoreApplication.translate("MainWindow", u"Right Leg", None))
        pass
    # retranslateUi

