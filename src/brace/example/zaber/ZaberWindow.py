# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'mainwindowZaberrtQMTf.ui'
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
from PySide6.QtWidgets import (QAbstractScrollArea, QApplication, QDoubleSpinBox, QFrame,
    QGridLayout, QGroupBox, QHBoxLayout, QLabel,
    QMainWindow, QMenu, QMenuBar, QPushButton,
    QSizePolicy, QStatusBar, QTabWidget, QTextBrowser,
    QTextEdit, QToolBar, QVBoxLayout, QWidget)

from pyqtgraph import GraphicsLayoutWidget

class Ui_ZaberWindow(object):
    def setupUi(self, ZaberWindow):
        if not ZaberWindow.objectName():
            ZaberWindow.setObjectName(u"ZaberWindow")
        ZaberWindow.resize(1600, 900)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(ZaberWindow.sizePolicy().hasHeightForWidth())
        ZaberWindow.setSizePolicy(sizePolicy)
        ZaberWindow.setWindowTitle(u"Zaber Graphing Example")
#if QT_CONFIG(tooltip)
        ZaberWindow.setToolTip(u"")
#endif // QT_CONFIG(tooltip)
        self.actionSaveData = QAction(ZaberWindow)
        self.actionSaveData.setObjectName(u"actionSaveData")
        icon = QIcon(QIcon.fromTheme(QIcon.ThemeIcon.DocumentSaveAs))
        self.actionSaveData.setIcon(icon)
        font = QFont()
        self.actionSaveData.setFont(font)
        self.actionExit = QAction(ZaberWindow)
        self.actionExit.setObjectName(u"actionExit")
        icon1 = QIcon(QIcon.fromTheme(QIcon.ThemeIcon.ApplicationExit))
        self.actionExit.setIcon(icon1)
        self.actionExit.setText(u"Exit")
        self.actionExit.setFont(font)
        self.actionLightMode = QAction(ZaberWindow)
        self.actionLightMode.setObjectName(u"actionLightMode")
        self.actionLightMode.setCheckable(True)
        self.actionLightMode.setChecked(False)
        self.actionLightMode.setText(u"Light Mode")
        self.actionLightMode.setFont(font)
        self.actionDarkMode = QAction(ZaberWindow)
        self.actionDarkMode.setObjectName(u"actionDarkMode")
        self.actionDarkMode.setCheckable(True)
        self.actionDarkMode.setText(u"Dark Mode")
        self.actionDarkMode.setFont(font)
        self.actionSystemDefault = QAction(ZaberWindow)
        self.actionSystemDefault.setObjectName(u"actionSystemDefault")
        self.actionSystemDefault.setCheckable(True)
        self.actionSystemDefault.setChecked(True)
        self.actionSystemDefault.setText(u"System Default")
        self.actionSystemDefault.setFont(font)
        self.actionOpenData = QAction(ZaberWindow)
        self.actionOpenData.setObjectName(u"actionOpenData")
        icon2 = QIcon(QIcon.fromTheme(QIcon.ThemeIcon.DocumentOpen))
        self.actionOpenData.setIcon(icon2)
        self.actionOpenData.setFont(font)
        self.centralwidget = QWidget(ZaberWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        sizePolicy.setHeightForWidth(self.centralwidget.sizePolicy().hasHeightForWidth())
        self.centralwidget.setSizePolicy(sizePolicy)
        self.gridLayout = QGridLayout(self.centralwidget)
        self.gridLayout.setObjectName(u"gridLayout")
        self.plotTabWidget = QTabWidget(self.centralwidget)
        self.plotTabWidget.setObjectName(u"plotTabWidget")
        sizePolicy.setHeightForWidth(self.plotTabWidget.sizePolicy().hasHeightForWidth())
        self.plotTabWidget.setSizePolicy(sizePolicy)
        font1 = QFont()
        font1.setFamilies([u"Microsoft Sans Serif"])
        self.plotTabWidget.setFont(font1)
        self.plotTabWidget.setCursor(QCursor(Qt.CursorShape.ArrowCursor))
        self.proportionalPlotsTab = QWidget()
        self.proportionalPlotsTab.setObjectName(u"proportionalPlotsTab")
        self.proportionalPlotTabGridLayout = QGridLayout(self.proportionalPlotsTab)
        self.proportionalPlotTabGridLayout.setObjectName(u"proportionalPlotTabGridLayout")
        self.proportionalGraphWidget = GraphicsLayoutWidget(self.proportionalPlotsTab)
        self.proportionalGraphWidget.setObjectName(u"proportionalGraphWidget")
        sizePolicy.setHeightForWidth(self.proportionalGraphWidget.sizePolicy().hasHeightForWidth())
        self.proportionalGraphWidget.setSizePolicy(sizePolicy)
        self.proportionalGraphWidget.setFont(font1)
        self.proportionalGraphWidget.setAcceptDrops(False)
#if QT_CONFIG(tooltip)
        self.proportionalGraphWidget.setToolTip(u"")
#endif // QT_CONFIG(tooltip)

        self.proportionalPlotTabGridLayout.addWidget(self.proportionalGraphWidget, 0, 0, 1, 1)

        self.proportionalGraphToggleHorizontalLayout = QHBoxLayout()
        self.proportionalGraphToggleHorizontalLayout.setObjectName(u"proportionalGraphToggleHorizontalLayout")

        self.proportionalPlotTabGridLayout.addLayout(self.proportionalGraphToggleHorizontalLayout, 1, 0, 1, 1)

        self.proportionalPlotTabGridLayout.setRowStretch(0, 9)
        self.plotTabWidget.addTab(self.proportionalPlotsTab, "")

        self.gridLayout.addWidget(self.plotTabWidget, 0, 0, 1, 1)

        self.rightSideVerticalLayout = QVBoxLayout()
        self.rightSideVerticalLayout.setObjectName(u"rightSideVerticalLayout")
        self.statusGroupBox = QGroupBox(self.centralwidget)
        self.statusGroupBox.setObjectName(u"statusGroupBox")
        sizePolicy.setHeightForWidth(self.statusGroupBox.sizePolicy().hasHeightForWidth())
        self.statusGroupBox.setSizePolicy(sizePolicy)
        self.statusGroupBox.setFont(font1)
        self.statusGroupBox.setCursor(QCursor(Qt.CursorShape.IBeamCursor))
        self.statusGroupBox.setTitle(u"Status")
        self.statusGroupBoxVerticalLayout = QVBoxLayout(self.statusGroupBox)
        self.statusGroupBoxVerticalLayout.setObjectName(u"statusGroupBoxVerticalLayout")
        self.statusTextBrowser = QTextBrowser(self.statusGroupBox)
        self.statusTextBrowser.setObjectName(u"statusTextBrowser")
        sizePolicy.setHeightForWidth(self.statusTextBrowser.sizePolicy().hasHeightForWidth())
        self.statusTextBrowser.setSizePolicy(sizePolicy)
        self.statusTextBrowser.setFont(font1)
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
"</style></head><body style=\" font-family:'Microsoft Sans Serif'; font-size:9pt; font-weight:400; font-style:normal;\">\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-family:'Segoe UI'; font-size:10pt;\"><br /></p></body></html>")
        self.statusTextBrowser.setTextInteractionFlags(Qt.TextInteractionFlag.LinksAccessibleByKeyboard|Qt.TextInteractionFlag.LinksAccessibleByMouse|Qt.TextInteractionFlag.TextBrowserInteraction|Qt.TextInteractionFlag.TextSelectableByKeyboard|Qt.TextInteractionFlag.TextSelectableByMouse)

        self.statusGroupBoxVerticalLayout.addWidget(self.statusTextBrowser)


        self.rightSideVerticalLayout.addWidget(self.statusGroupBox)

        self.sessionConnectHorizontalLayout = QHBoxLayout()
        self.sessionConnectHorizontalLayout.setObjectName(u"sessionConnectHorizontalLayout")
        self.sessionGroupBox = QGroupBox(self.centralwidget)
        self.sessionGroupBox.setObjectName(u"sessionGroupBox")
        sizePolicy.setHeightForWidth(self.sessionGroupBox.sizePolicy().hasHeightForWidth())
        self.sessionGroupBox.setSizePolicy(sizePolicy)
        self.sessionGroupBox.setMinimumSize(QSize(0, 0))
        self.sessionGroupBox.setFont(font1)
        self.sessionGroupBox.setTitle(u"Session")
        self.connectGroupBoxVerticalLayout = QVBoxLayout(self.sessionGroupBox)
        self.connectGroupBoxVerticalLayout.setSpacing(3)
        self.connectGroupBoxVerticalLayout.setObjectName(u"connectGroupBoxVerticalLayout")
        self.connectGroupBoxVerticalLayout.setContentsMargins(-1, 6, -1, 6)
        self.setCalibrationButton = QPushButton(self.sessionGroupBox)
        self.setCalibrationButton.setObjectName(u"setCalibrationButton")
        sizePolicy.setHeightForWidth(self.setCalibrationButton.sizePolicy().hasHeightForWidth())
        self.setCalibrationButton.setSizePolicy(sizePolicy)
        self.setCalibrationButton.setFont(font1)
        self.setCalibrationButton.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setCalibrationButton.setText(u"Set Calibration")

        self.connectGroupBoxVerticalLayout.addWidget(self.setCalibrationButton)

        self.enableActuationButton = QPushButton(self.sessionGroupBox)
        self.enableActuationButton.setObjectName(u"enableActuationButton")
        sizePolicy.setHeightForWidth(self.enableActuationButton.sizePolicy().hasHeightForWidth())
        self.enableActuationButton.setSizePolicy(sizePolicy)
        font2 = QFont()
        font2.setFamilies([u"Microsoft Sans Serif"])
        font2.setBold(False)
        self.enableActuationButton.setFont(font2)
        self.enableActuationButton.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.enableActuationButton.setText(u"Enable Actuation")
        self.enableActuationButton.setCheckable(True)

        self.connectGroupBoxVerticalLayout.addWidget(self.enableActuationButton)

        self.invertPushButton = QPushButton(self.sessionGroupBox)
        self.invertPushButton.setObjectName(u"invertPushButton")
        sizePolicy.setHeightForWidth(self.invertPushButton.sizePolicy().hasHeightForWidth())
        self.invertPushButton.setSizePolicy(sizePolicy)
        self.invertPushButton.setFont(font1)
        self.invertPushButton.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.invertPushButton.setCheckable(True)

        self.connectGroupBoxVerticalLayout.addWidget(self.invertPushButton)

        self.connectGroupBoxVerticalLayout.setStretch(0, 1)
        self.connectGroupBoxVerticalLayout.setStretch(1, 1)
        self.connectGroupBoxVerticalLayout.setStretch(2, 1)

        self.sessionConnectHorizontalLayout.addWidget(self.sessionGroupBox)

        self.connectGroupBox = QGroupBox(self.centralwidget)
        self.connectGroupBox.setObjectName(u"connectGroupBox")
        sizePolicy.setHeightForWidth(self.connectGroupBox.sizePolicy().hasHeightForWidth())
        self.connectGroupBox.setSizePolicy(sizePolicy)
        self.connectGroupBox.setFont(font2)
        self.connectGroupBox.setTitle(u"Connect")
        self.sessionGroupVerticalLayout = QVBoxLayout(self.connectGroupBox)
        self.sessionGroupVerticalLayout.setSpacing(3)
        self.sessionGroupVerticalLayout.setObjectName(u"sessionGroupVerticalLayout")
        self.sessionGroupVerticalLayout.setContentsMargins(-1, 6, -1, 6)
        self.connectToZaberButton = QPushButton(self.connectGroupBox)
        self.connectToZaberButton.setObjectName(u"connectToZaberButton")
        sizePolicy.setHeightForWidth(self.connectToZaberButton.sizePolicy().hasHeightForWidth())
        self.connectToZaberButton.setSizePolicy(sizePolicy)
        font3 = QFont()
        font3.setFamilies([u"Microsoft Sans Serif"])
        font3.setPointSize(10)
        font3.setBold(False)
        self.connectToZaberButton.setFont(font3)
        self.connectToZaberButton.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.connectToZaberButton.setText(u"Connect to Zaber Controller")

        self.sessionGroupVerticalLayout.addWidget(self.connectToZaberButton)

        self.startStreamPushButton = QPushButton(self.connectGroupBox)
        self.startStreamPushButton.setObjectName(u"startStreamPushButton")
        sizePolicy.setHeightForWidth(self.startStreamPushButton.sizePolicy().hasHeightForWidth())
        self.startStreamPushButton.setSizePolicy(sizePolicy)
        self.startStreamPushButton.setFont(font3)
        self.startStreamPushButton.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.startStreamPushButton.setText(u"Start Stream")
        self.startStreamPushButton.setCheckable(True)
        self.startStreamPushButton.setAutoDefault(True)

        self.sessionGroupVerticalLayout.addWidget(self.startStreamPushButton)


        self.sessionConnectHorizontalLayout.addWidget(self.connectGroupBox)

        self.sessionConnectHorizontalLayout.setStretch(0, 1)
        self.sessionConnectHorizontalLayout.setStretch(1, 2)

        self.rightSideVerticalLayout.addLayout(self.sessionConnectHorizontalLayout)

        self.configurationBox = QGroupBox(self.centralwidget)
        self.configurationBox.setObjectName(u"configurationBox")
        sizePolicy.setHeightForWidth(self.configurationBox.sizePolicy().hasHeightForWidth())
        self.configurationBox.setSizePolicy(sizePolicy)
        self.configurationBox.setFont(font1)
        self.configurationBox.setTitle(u"Configuration")
        self.verticalLayout = QVBoxLayout(self.configurationBox)
        self.verticalLayout.setSpacing(3)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(-1, 3, -1, 3)
        self.configurationTabs = QTabWidget(self.configurationBox)
        self.configurationTabs.setObjectName(u"configurationTabs")
        sizePolicy.setHeightForWidth(self.configurationTabs.sizePolicy().hasHeightForWidth())
        self.configurationTabs.setSizePolicy(sizePolicy)
        self.configurationTabs.setFont(font1)
        self.configurationTabs.setCursor(QCursor(Qt.CursorShape.ArrowCursor))
        self.configurationTabs.setStyleSheet(u"")
        self.configurationTabs.setTabShape(QTabWidget.TabShape.Rounded)
        self.configurationTabs.setIconSize(QSize(0, 0))
        self.configurationTabs.setElideMode(Qt.TextElideMode.ElideNone)
        self.configurationTabs.setUsesScrollButtons(False)
        self.configurationTabs.setTabsClosable(False)
        self.configurationTabs.setMovable(False)
        self.configurationTabs.setTabBarAutoHide(False)
        self.proportionalPage = QWidget()
        self.proportionalPage.setObjectName(u"proportionalPage")
        self.proportionalPageGridLayout = QGridLayout(self.proportionalPage)
        self.proportionalPageGridLayout.setObjectName(u"proportionalPageGridLayout")
        self.proportionalSubPages = QTabWidget(self.proportionalPage)
        self.proportionalSubPages.setObjectName(u"proportionalSubPages")
        sizePolicy.setHeightForWidth(self.proportionalSubPages.sizePolicy().hasHeightForWidth())
        self.proportionalSubPages.setSizePolicy(sizePolicy)
        self.proportionalSubPages.setMinimumSize(QSize(0, 0))
        self.proportionalSubPages.setFont(font1)
        self.proportionalSubPages.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.proportionalSubPages.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.proportionalSubPages.setStyleSheet(u"")
        self.proportionalPositionLimitsPage = QWidget()
        self.proportionalPositionLimitsPage.setObjectName(u"proportionalPositionLimitsPage")
        sizePolicy.setHeightForWidth(self.proportionalPositionLimitsPage.sizePolicy().hasHeightForWidth())
        self.proportionalPositionLimitsPage.setSizePolicy(sizePolicy)
        self.proportionalPositionGridLayout = QGridLayout(self.proportionalPositionLimitsPage)
        self.proportionalPositionGridLayout.setObjectName(u"proportionalPositionGridLayout")
        self.proportionalMinPositionLimitLabel = QLabel(self.proportionalPositionLimitsPage)
        self.proportionalMinPositionLimitLabel.setObjectName(u"proportionalMinPositionLimitLabel")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.proportionalMinPositionLimitLabel.sizePolicy().hasHeightForWidth())
        self.proportionalMinPositionLimitLabel.setSizePolicy(sizePolicy1)
        font4 = QFont()
        font4.setFamilies([u"Microsoft Sans Serif"])
        font4.setPointSize(9)
        self.proportionalMinPositionLimitLabel.setFont(font4)
#if QT_CONFIG(tooltip)
        self.proportionalMinPositionLimitLabel.setToolTip(u"")
#endif // QT_CONFIG(tooltip)
        self.proportionalMinPositionLimitLabel.setText(u"Minimum Position Limit")

        self.proportionalPositionGridLayout.addWidget(self.proportionalMinPositionLimitLabel, 0, 0, 1, 1)

        self.proportionalMinPositionLimitUnitLabel = QLabel(self.proportionalPositionLimitsPage)
        self.proportionalMinPositionLimitUnitLabel.setObjectName(u"proportionalMinPositionLimitUnitLabel")
        self.proportionalMinPositionLimitUnitLabel.setFont(font4)
        self.proportionalMinPositionLimitUnitLabel.setText(u"mm")
        self.proportionalMinPositionLimitUnitLabel.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.proportionalPositionGridLayout.addWidget(self.proportionalMinPositionLimitUnitLabel, 0, 2, 1, 1)

        self.proportionalMaxPositionLimitLabel = QLabel(self.proportionalPositionLimitsPage)
        self.proportionalMaxPositionLimitLabel.setObjectName(u"proportionalMaxPositionLimitLabel")
        self.proportionalMaxPositionLimitLabel.setEnabled(True)
        sizePolicy1.setHeightForWidth(self.proportionalMaxPositionLimitLabel.sizePolicy().hasHeightForWidth())
        self.proportionalMaxPositionLimitLabel.setSizePolicy(sizePolicy1)
        self.proportionalMaxPositionLimitLabel.setFont(font4)
#if QT_CONFIG(tooltip)
        self.proportionalMaxPositionLimitLabel.setToolTip(u"Flexion angle should be considered more positive.")
#endif // QT_CONFIG(tooltip)
        self.proportionalMaxPositionLimitLabel.setText(u"Maximum Position Limit")

        self.proportionalPositionGridLayout.addWidget(self.proportionalMaxPositionLimitLabel, 1, 0, 1, 1)

        self.proportionalMaxPositionLimitUnitLabel = QLabel(self.proportionalPositionLimitsPage)
        self.proportionalMaxPositionLimitUnitLabel.setObjectName(u"proportionalMaxPositionLimitUnitLabel")
        self.proportionalMaxPositionLimitUnitLabel.setFont(font4)
        self.proportionalMaxPositionLimitUnitLabel.setText(u"mm")
        self.proportionalMaxPositionLimitUnitLabel.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.proportionalPositionGridLayout.addWidget(self.proportionalMaxPositionLimitUnitLabel, 1, 2, 1, 1)

        self.proportionalMinPositionLimitDoubleSpinBox = QDoubleSpinBox(self.proportionalPositionLimitsPage)
        self.proportionalMinPositionLimitDoubleSpinBox.setObjectName(u"proportionalMinPositionLimitDoubleSpinBox")
        self.proportionalMinPositionLimitDoubleSpinBox.setCursor(QCursor(Qt.CursorShape.IBeamCursor))

        self.proportionalPositionGridLayout.addWidget(self.proportionalMinPositionLimitDoubleSpinBox, 0, 1, 1, 1)

        self.proportionalMaxPositionLimitDoubleSpinBox = QDoubleSpinBox(self.proportionalPositionLimitsPage)
        self.proportionalMaxPositionLimitDoubleSpinBox.setObjectName(u"proportionalMaxPositionLimitDoubleSpinBox")
        self.proportionalMaxPositionLimitDoubleSpinBox.setCursor(QCursor(Qt.CursorShape.IBeamCursor))

        self.proportionalPositionGridLayout.addWidget(self.proportionalMaxPositionLimitDoubleSpinBox, 1, 1, 1, 1)

        self.proportionalSubPages.addTab(self.proportionalPositionLimitsPage, "")
        self.proportionalSubPages.setTabText(self.proportionalSubPages.indexOf(self.proportionalPositionLimitsPage), u"Position Limits")
        self.proportionalLoadCellLimitsPage = QWidget()
        self.proportionalLoadCellLimitsPage.setObjectName(u"proportionalLoadCellLimitsPage")
        self.proportionalLoadCellGridLayout = QGridLayout(self.proportionalLoadCellLimitsPage)
        self.proportionalLoadCellGridLayout.setObjectName(u"proportionalLoadCellGridLayout")
        self.proportionalMinLoadCellLabel = QLabel(self.proportionalLoadCellLimitsPage)
        self.proportionalMinLoadCellLabel.setObjectName(u"proportionalMinLoadCellLabel")
        sizePolicy1.setHeightForWidth(self.proportionalMinLoadCellLabel.sizePolicy().hasHeightForWidth())
        self.proportionalMinLoadCellLabel.setSizePolicy(sizePolicy1)
        self.proportionalMinLoadCellLabel.setFont(font1)
        self.proportionalMinLoadCellLabel.setText(u"Minimum Load Cell Limit")

        self.proportionalLoadCellGridLayout.addWidget(self.proportionalMinLoadCellLabel, 0, 0, 1, 1)

        self.proportionalMinLoadCellDoubleSpinBox = QDoubleSpinBox(self.proportionalLoadCellLimitsPage)
        self.proportionalMinLoadCellDoubleSpinBox.setObjectName(u"proportionalMinLoadCellDoubleSpinBox")
        sizePolicy2 = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.proportionalMinLoadCellDoubleSpinBox.sizePolicy().hasHeightForWidth())
        self.proportionalMinLoadCellDoubleSpinBox.setSizePolicy(sizePolicy2)
        self.proportionalMinLoadCellDoubleSpinBox.setFont(font1)
        self.proportionalMinLoadCellDoubleSpinBox.setCursor(QCursor(Qt.CursorShape.IBeamCursor))
        self.proportionalMinLoadCellDoubleSpinBox.setWrapping(False)
        self.proportionalMinLoadCellDoubleSpinBox.setSpecialValueText(u"")
        self.proportionalMinLoadCellDoubleSpinBox.setAccelerated(True)
        self.proportionalMinLoadCellDoubleSpinBox.setProperty(u"showGroupSeparator", False)
        self.proportionalMinLoadCellDoubleSpinBox.setDecimals(2)
        self.proportionalMinLoadCellDoubleSpinBox.setMinimum(-100.000000000000000)
        self.proportionalMinLoadCellDoubleSpinBox.setMaximum(100.000000000000000)
        self.proportionalMinLoadCellDoubleSpinBox.setSingleStep(1.000000000000000)
        self.proportionalMinLoadCellDoubleSpinBox.setValue(0.000000000000000)

        self.proportionalLoadCellGridLayout.addWidget(self.proportionalMinLoadCellDoubleSpinBox, 0, 1, 1, 1)

        self.proportionalMinLoadCellUnitLabel = QLabel(self.proportionalLoadCellLimitsPage)
        self.proportionalMinLoadCellUnitLabel.setObjectName(u"proportionalMinLoadCellUnitLabel")
        sizePolicy.setHeightForWidth(self.proportionalMinLoadCellUnitLabel.sizePolicy().hasHeightForWidth())
        self.proportionalMinLoadCellUnitLabel.setSizePolicy(sizePolicy)
        self.proportionalMinLoadCellUnitLabel.setFont(font1)
        self.proportionalMinLoadCellUnitLabel.setText(u"g")
        self.proportionalMinLoadCellUnitLabel.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.proportionalLoadCellGridLayout.addWidget(self.proportionalMinLoadCellUnitLabel, 0, 2, 1, 1)

        self.proportionalMaxLoadCellLabel = QLabel(self.proportionalLoadCellLimitsPage)
        self.proportionalMaxLoadCellLabel.setObjectName(u"proportionalMaxLoadCellLabel")
        sizePolicy1.setHeightForWidth(self.proportionalMaxLoadCellLabel.sizePolicy().hasHeightForWidth())
        self.proportionalMaxLoadCellLabel.setSizePolicy(sizePolicy1)
        self.proportionalMaxLoadCellLabel.setFont(font1)
        self.proportionalMaxLoadCellLabel.setText(u"Maximum Load Cell Limit")

        self.proportionalLoadCellGridLayout.addWidget(self.proportionalMaxLoadCellLabel, 1, 0, 1, 1)

        self.proportionalMaxLoadCellDoubleSpinBox = QDoubleSpinBox(self.proportionalLoadCellLimitsPage)
        self.proportionalMaxLoadCellDoubleSpinBox.setObjectName(u"proportionalMaxLoadCellDoubleSpinBox")
        sizePolicy2.setHeightForWidth(self.proportionalMaxLoadCellDoubleSpinBox.sizePolicy().hasHeightForWidth())
        self.proportionalMaxLoadCellDoubleSpinBox.setSizePolicy(sizePolicy2)
        self.proportionalMaxLoadCellDoubleSpinBox.setFont(font1)
        self.proportionalMaxLoadCellDoubleSpinBox.setCursor(QCursor(Qt.CursorShape.IBeamCursor))
        self.proportionalMaxLoadCellDoubleSpinBox.setWrapping(False)
        self.proportionalMaxLoadCellDoubleSpinBox.setSpecialValueText(u"")
        self.proportionalMaxLoadCellDoubleSpinBox.setAccelerated(True)
        self.proportionalMaxLoadCellDoubleSpinBox.setProperty(u"showGroupSeparator", False)
        self.proportionalMaxLoadCellDoubleSpinBox.setDecimals(2)
        self.proportionalMaxLoadCellDoubleSpinBox.setMinimum(-100.000000000000000)
        self.proportionalMaxLoadCellDoubleSpinBox.setMaximum(100.000000000000000)
        self.proportionalMaxLoadCellDoubleSpinBox.setSingleStep(1.000000000000000)
        self.proportionalMaxLoadCellDoubleSpinBox.setValue(0.000000000000000)

        self.proportionalLoadCellGridLayout.addWidget(self.proportionalMaxLoadCellDoubleSpinBox, 1, 1, 1, 1)

        self.proportionalMaxLoadCellUnitLabel = QLabel(self.proportionalLoadCellLimitsPage)
        self.proportionalMaxLoadCellUnitLabel.setObjectName(u"proportionalMaxLoadCellUnitLabel")
        sizePolicy.setHeightForWidth(self.proportionalMaxLoadCellUnitLabel.sizePolicy().hasHeightForWidth())
        self.proportionalMaxLoadCellUnitLabel.setSizePolicy(sizePolicy)
        self.proportionalMaxLoadCellUnitLabel.setFont(font4)
        self.proportionalMaxLoadCellUnitLabel.setText(u"g")
        self.proportionalMaxLoadCellUnitLabel.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.proportionalLoadCellGridLayout.addWidget(self.proportionalMaxLoadCellUnitLabel, 1, 2, 1, 1)

        self.proportionalSubPages.addTab(self.proportionalLoadCellLimitsPage, "")
        self.proportionalSubPages.setTabText(self.proportionalSubPages.indexOf(self.proportionalLoadCellLimitsPage), u"Load Cell Limits")

        self.proportionalPageGridLayout.addWidget(self.proportionalSubPages, 0, 0, 1, 1)

        self.configurationTabs.addTab(self.proportionalPage, "")

        self.verticalLayout.addWidget(self.configurationTabs)

        self.configurationButtonsVerticalLayout = QVBoxLayout()
        self.configurationButtonsVerticalLayout.setObjectName(u"configurationButtonsVerticalLayout")
        self.configurationReadWriteHorizontalLayout = QHBoxLayout()
        self.configurationReadWriteHorizontalLayout.setObjectName(u"configurationReadWriteHorizontalLayout")
        self.readConfigurationButton = QPushButton(self.configurationBox)
        self.readConfigurationButton.setObjectName(u"readConfigurationButton")
        sizePolicy.setHeightForWidth(self.readConfigurationButton.sizePolicy().hasHeightForWidth())
        self.readConfigurationButton.setSizePolicy(sizePolicy)
        font5 = QFont()
        font5.setFamilies([u"Microsoft Sans Serif"])
        font5.setPointSize(10)
        self.readConfigurationButton.setFont(font5)
        self.readConfigurationButton.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.readConfigurationButton.setText(u"Read Configuration from Remote")

        self.configurationReadWriteHorizontalLayout.addWidget(self.readConfigurationButton)

        self.writeChangesButton = QPushButton(self.configurationBox)
        self.writeChangesButton.setObjectName(u"writeChangesButton")
        sizePolicy.setHeightForWidth(self.writeChangesButton.sizePolicy().hasHeightForWidth())
        self.writeChangesButton.setSizePolicy(sizePolicy)
        self.writeChangesButton.setFont(font5)
        self.writeChangesButton.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.writeChangesButton.setText(u"Write Changes to Remote")

        self.configurationReadWriteHorizontalLayout.addWidget(self.writeChangesButton)

        self.configurationReadWriteHorizontalLayout.setStretch(0, 1)
        self.configurationReadWriteHorizontalLayout.setStretch(1, 1)

        self.configurationButtonsVerticalLayout.addLayout(self.configurationReadWriteHorizontalLayout)


        self.verticalLayout.addLayout(self.configurationButtonsVerticalLayout)

        self.verticalLayout.setStretch(0, 6)
        self.verticalLayout.setStretch(1, 1)

        self.rightSideVerticalLayout.addWidget(self.configurationBox)

        self.rightSideVerticalLayout.setStretch(0, 3)
        self.rightSideVerticalLayout.setStretch(1, 1)
        self.rightSideVerticalLayout.setStretch(2, 2)

        self.gridLayout.addLayout(self.rightSideVerticalLayout, 0, 1, 1, 1)

        self.gridLayout.setColumnStretch(0, 2)
        self.gridLayout.setColumnStretch(1, 1)
        ZaberWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(ZaberWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 1600, 33))
        font6 = QFont()
        font6.setPointSize(9)
        self.menubar.setFont(font6)
        self.menuMenu = QMenu(self.menubar)
        self.menuMenu.setObjectName(u"menuMenu")
        self.menuMenu.setFont(font6)
        self.menuMenu.setTitle(u"File")
        ZaberWindow.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(ZaberWindow)
        self.statusbar.setObjectName(u"statusbar")
        ZaberWindow.setStatusBar(self.statusbar)
        self.toolBar = QToolBar(ZaberWindow)
        self.toolBar.setObjectName(u"toolBar")
        ZaberWindow.addToolBar(Qt.ToolBarArea.TopToolBarArea, self.toolBar)
        QWidget.setTabOrder(self.configurationTabs, self.proportionalMinLoadCellDoubleSpinBox)
        QWidget.setTabOrder(self.proportionalMinLoadCellDoubleSpinBox, self.proportionalMaxLoadCellDoubleSpinBox)
        QWidget.setTabOrder(self.proportionalMaxLoadCellDoubleSpinBox, self.readConfigurationButton)
        QWidget.setTabOrder(self.readConfigurationButton, self.writeChangesButton)
        QWidget.setTabOrder(self.writeChangesButton, self.startStreamPushButton)
        QWidget.setTabOrder(self.startStreamPushButton, self.statusTextBrowser)
        QWidget.setTabOrder(self.statusTextBrowser, self.plotTabWidget)

        self.menubar.addAction(self.menuMenu.menuAction())
        self.menuMenu.addSeparator()
        self.menuMenu.addSeparator()
        self.menuMenu.addAction(self.actionSaveData)
        self.menuMenu.addAction(self.actionOpenData)
        self.menuMenu.addAction(self.actionExit)

        self.retranslateUi(ZaberWindow)
        self.actionExit.triggered.connect(ZaberWindow.close)

        self.plotTabWidget.setCurrentIndex(0)
        self.startStreamPushButton.setDefault(True)
        self.configurationTabs.setCurrentIndex(0)
        self.proportionalSubPages.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(ZaberWindow)
    # setupUi

    def retranslateUi(self, ZaberWindow):
        self.actionSaveData.setText(QCoreApplication.translate("ZaberWindow", u"Save Data As...", None))
        self.actionSaveData.setIconText(QCoreApplication.translate("ZaberWindow", u"Save As", None))
#if QT_CONFIG(shortcut)
        self.actionSaveData.setShortcut(QCoreApplication.translate("ZaberWindow", u"Ctrl+S", None))
#endif // QT_CONFIG(shortcut)
        self.actionOpenData.setText(QCoreApplication.translate("ZaberWindow", u"Open Data", None))
#if QT_CONFIG(shortcut)
        self.actionOpenData.setShortcut(QCoreApplication.translate("ZaberWindow", u"Ctrl+O", None))
#endif // QT_CONFIG(shortcut)
        self.plotTabWidget.setTabText(self.plotTabWidget.indexOf(self.proportionalPlotsTab), QCoreApplication.translate("ZaberWindow", u"Proportional", None))
        self.invertPushButton.setText(QCoreApplication.translate("ZaberWindow", u"Invert Position", None))
        self.configurationTabs.setTabText(self.configurationTabs.indexOf(self.proportionalPage), QCoreApplication.translate("ZaberWindow", u"Proportional", None))
        self.toolBar.setWindowTitle(QCoreApplication.translate("ZaberWindow", u"toolBar", None))
        pass
    # retranslateUi

