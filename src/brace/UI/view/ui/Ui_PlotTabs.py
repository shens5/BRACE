# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'plotTabsrmnFeW.ui'
##
## Created by: Qt User Interface Compiler version 6.9.0
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QGridLayout, QHBoxLayout, QSizePolicy,
    QTabWidget, QWidget)

from brace.UI.PlotConfiguration.ConfigurePlotHelpers import HideableElementsGraphicsLayoutWidget

class Ui_PlotsPage(object):
    def setupUi(self, PlotsPage):
        if not PlotsPage.objectName():
            PlotsPage.setObjectName(u"PlotsPage")
        PlotsPage.resize(998, 829)
        self.gridLayout = QGridLayout(PlotsPage)
        self.gridLayout.setObjectName(u"gridLayout")
        self.plotTabWidget = QTabWidget(PlotsPage)
        self.plotTabWidget.setObjectName(u"plotTabWidget")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.plotTabWidget.sizePolicy().hasHeightForWidth())
        self.plotTabWidget.setSizePolicy(sizePolicy)
        font = QFont()
        font.setPointSize(9)
        self.plotTabWidget.setFont(font)
        self.plotTabWidget.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.walkFSM5PlotsTab = QWidget()
        self.walkFSM5PlotsTab.setObjectName(u"walkFSM5PlotsTab")
        self.walkFSM5PlotsTabGridLayout = QGridLayout(self.walkFSM5PlotsTab)
        self.walkFSM5PlotsTabGridLayout.setObjectName(u"walkFSM5PlotsTabGridLayout")
        self.walkFSM5GraphWidget = HideableElementsGraphicsLayoutWidget(self.walkFSM5PlotsTab)
        self.walkFSM5GraphWidget.setObjectName(u"walkFSM5GraphWidget")
        sizePolicy.setHeightForWidth(self.walkFSM5GraphWidget.sizePolicy().hasHeightForWidth())
        self.walkFSM5GraphWidget.setSizePolicy(sizePolicy)
        font1 = QFont()
        font1.setPointSize(11)
        self.walkFSM5GraphWidget.setFont(font1)
        self.walkFSM5GraphWidget.setAcceptDrops(False)
#if QT_CONFIG(tooltip)
        self.walkFSM5GraphWidget.setToolTip(u"")
#endif // QT_CONFIG(tooltip)

        self.walkFSM5PlotsTabGridLayout.addWidget(self.walkFSM5GraphWidget, 0, 0, 1, 1)

        self.walkFSM5GraphToggleHorizontalLayout = QHBoxLayout()
        self.walkFSM5GraphToggleHorizontalLayout.setObjectName(u"walkFSM5GraphToggleHorizontalLayout")

        self.walkFSM5PlotsTabGridLayout.addLayout(self.walkFSM5GraphToggleHorizontalLayout, 1, 0, 1, 1)

        self.walkFSM5PlotsTabGridLayout.setRowStretch(0, 9)
        self.walkFSM5PlotsTabGridLayout.setRowStretch(1, 1)
        self.plotTabWidget.addTab(self.walkFSM5PlotsTab, "")
        self.proportionalPlotsTab = QWidget()
        self.proportionalPlotsTab.setObjectName(u"proportionalPlotsTab")
        self.proportionalPlotTabGridLayout = QGridLayout(self.proportionalPlotsTab)
        self.proportionalPlotTabGridLayout.setObjectName(u"proportionalPlotTabGridLayout")
        self.proportionalGraphToggleHorizontalLayout = QHBoxLayout()
        self.proportionalGraphToggleHorizontalLayout.setObjectName(u"proportionalGraphToggleHorizontalLayout")

        self.proportionalPlotTabGridLayout.addLayout(self.proportionalGraphToggleHorizontalLayout, 1, 0, 1, 1)

        self.proportionalGraphWidget = HideableElementsGraphicsLayoutWidget(self.proportionalPlotsTab)
        self.proportionalGraphWidget.setObjectName(u"proportionalGraphWidget")
        sizePolicy.setHeightForWidth(self.proportionalGraphWidget.sizePolicy().hasHeightForWidth())
        self.proportionalGraphWidget.setSizePolicy(sizePolicy)
        self.proportionalGraphWidget.setFont(font1)
        self.proportionalGraphWidget.setAcceptDrops(False)
#if QT_CONFIG(tooltip)
        self.proportionalGraphWidget.setToolTip(u"")
#endif // QT_CONFIG(tooltip)

        self.proportionalPlotTabGridLayout.addWidget(self.proportionalGraphWidget, 0, 0, 1, 1)

        self.proportionalPlotTabGridLayout.setRowStretch(0, 9)
        self.proportionalPlotTabGridLayout.setRowStretch(1, 1)
        self.plotTabWidget.addTab(self.proportionalPlotsTab, "")
        self.standingPlotsTab = QWidget()
        self.standingPlotsTab.setObjectName(u"standingPlotsTab")
        self.standingPlotsGridLayout = QGridLayout(self.standingPlotsTab)
        self.standingPlotsGridLayout.setObjectName(u"standingPlotsGridLayout")
        self.standingGraphWidget = HideableElementsGraphicsLayoutWidget(self.standingPlotsTab)
        self.standingGraphWidget.setObjectName(u"standingGraphWidget")

        self.standingPlotsGridLayout.addWidget(self.standingGraphWidget, 0, 0, 1, 1)

        self.standingGraphToggleHorizontalLayout = QHBoxLayout()
        self.standingGraphToggleHorizontalLayout.setObjectName(u"standingGraphToggleHorizontalLayout")

        self.standingPlotsGridLayout.addLayout(self.standingGraphToggleHorizontalLayout, 1, 0, 1, 1)

        self.standingPlotsGridLayout.setRowStretch(0, 9)
        self.standingPlotsGridLayout.setRowStretch(1, 1)
        self.plotTabWidget.addTab(self.standingPlotsTab, "")

        self.gridLayout.addWidget(self.plotTabWidget, 0, 0, 1, 1)


        self.retranslateUi(PlotsPage)

        self.plotTabWidget.setCurrentIndex(2)


        QMetaObject.connectSlotsByName(PlotsPage)
    # setupUi

    def retranslateUi(self, PlotsPage):
        PlotsPage.setWindowTitle(QCoreApplication.translate("PlotsPage", u"Form", None))
        self.plotTabWidget.setTabText(self.plotTabWidget.indexOf(self.walkFSM5PlotsTab), QCoreApplication.translate("PlotsPage", u"Walk", None))
        self.plotTabWidget.setTabText(self.plotTabWidget.indexOf(self.proportionalPlotsTab), QCoreApplication.translate("PlotsPage", u"Proportional", None))
        self.plotTabWidget.setTabText(self.plotTabWidget.indexOf(self.standingPlotsTab), QCoreApplication.translate("PlotsPage", u"Standing", None))
    # retranslateUi

