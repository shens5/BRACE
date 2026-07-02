# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'simulatorConfigurationButtonsZNfPvo.ui'
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
from PySide6.QtWidgets import (QApplication, QGridLayout, QPushButton, QSizePolicy,
    QWidget)

class Ui_ConfigurationButtons(object):
    def setupUi(self, ConfigurationButtons):
        if not ConfigurationButtons.objectName():
            ConfigurationButtons.setObjectName(u"ConfigurationButtons")
        ConfigurationButtons.resize(361, 96)
        self.gridLayout = QGridLayout(ConfigurationButtons)
        self.gridLayout.setSpacing(0)
        self.gridLayout.setObjectName(u"gridLayout")
        self.gridLayout.setContentsMargins(0, 0, 0, 0)
        self.resetCurrentConfigurationPushButton = QPushButton(ConfigurationButtons)
        self.resetCurrentConfigurationPushButton.setObjectName(u"resetCurrentConfigurationPushButton")

        self.gridLayout.addWidget(self.resetCurrentConfigurationPushButton, 1, 0, 1, 1)

        self.saveCurrentConfigurationPushButton = QPushButton(ConfigurationButtons)
        self.saveCurrentConfigurationPushButton.setObjectName(u"saveCurrentConfigurationPushButton")

        self.gridLayout.addWidget(self.saveCurrentConfigurationPushButton, 2, 0, 1, 1)

        self.resetAllConfigurationPushButton = QPushButton(ConfigurationButtons)
        self.resetAllConfigurationPushButton.setObjectName(u"resetAllConfigurationPushButton")

        self.gridLayout.addWidget(self.resetAllConfigurationPushButton, 1, 1, 1, 1)

        self.loadDataFilePushButton = QPushButton(ConfigurationButtons)
        self.loadDataFilePushButton.setObjectName(u"loadDataFilePushButton")

        self.gridLayout.addWidget(self.loadDataFilePushButton, 2, 1, 1, 1)

        self.simulatePushButton = QPushButton(ConfigurationButtons)
        self.simulatePushButton.setObjectName(u"simulatePushButton")

        self.gridLayout.addWidget(self.simulatePushButton, 0, 0, 1, 2)


        self.retranslateUi(ConfigurationButtons)

        QMetaObject.connectSlotsByName(ConfigurationButtons)
    # setupUi

    def retranslateUi(self, ConfigurationButtons):
        ConfigurationButtons.setWindowTitle(QCoreApplication.translate("ConfigurationButtons", u"Form", None))
        self.resetCurrentConfigurationPushButton.setText(QCoreApplication.translate("ConfigurationButtons", u"Reset Current Configuration", None))
        self.saveCurrentConfigurationPushButton.setText(QCoreApplication.translate("ConfigurationButtons", u"Save Current Configuration", None))
        self.resetAllConfigurationPushButton.setText(QCoreApplication.translate("ConfigurationButtons", u"Reset All Configuration", None))
        self.loadDataFilePushButton.setText(QCoreApplication.translate("ConfigurationButtons", u"Load Data File", None))
        self.simulatePushButton.setText(QCoreApplication.translate("ConfigurationButtons", u"Simulate", None))
    # retranslateUi

