# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'windowConfigurationButtonsUACsvG.ui'
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
        ConfigurationButtons.resize(415, 92)
        self.gridLayout = QGridLayout(ConfigurationButtons)
        self.gridLayout.setObjectName(u"gridLayout")
        self.configurationButtonsGridLayout = QGridLayout()
        self.configurationButtonsGridLayout.setSpacing(0)
        self.configurationButtonsGridLayout.setObjectName(u"configurationButtonsGridLayout")
        self.saveConfigurationToFileButton = QPushButton(ConfigurationButtons)
        self.saveConfigurationToFileButton.setObjectName(u"saveConfigurationToFileButton")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.saveConfigurationToFileButton.sizePolicy().hasHeightForWidth())
        self.saveConfigurationToFileButton.setSizePolicy(sizePolicy)
        self.saveConfigurationToFileButton.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.saveConfigurationToFileButton.setText(u"Save Configuration to File")

        self.configurationButtonsGridLayout.addWidget(self.saveConfigurationToFileButton, 1, 1, 1, 1)

        self.writeChangesButton = QPushButton(ConfigurationButtons)
        self.writeChangesButton.setObjectName(u"writeChangesButton")
        sizePolicy.setHeightForWidth(self.writeChangesButton.sizePolicy().hasHeightForWidth())
        self.writeChangesButton.setSizePolicy(sizePolicy)
        self.writeChangesButton.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.writeChangesButton.setText(u"Write Current Controller Changes")

        self.configurationButtonsGridLayout.addWidget(self.writeChangesButton, 0, 1, 1, 1)

        self.loadConfigurationFromFileButton = QPushButton(ConfigurationButtons)
        self.loadConfigurationFromFileButton.setObjectName(u"loadConfigurationFromFileButton")
        sizePolicy.setHeightForWidth(self.loadConfigurationFromFileButton.sizePolicy().hasHeightForWidth())
        self.loadConfigurationFromFileButton.setSizePolicy(sizePolicy)
        self.loadConfigurationFromFileButton.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.loadConfigurationFromFileButton.setText(u"Load Configuration from File")

        self.configurationButtonsGridLayout.addWidget(self.loadConfigurationFromFileButton, 1, 0, 1, 1)

        self.readConfigurationButton = QPushButton(ConfigurationButtons)
        self.readConfigurationButton.setObjectName(u"readConfigurationButton")
        sizePolicy.setHeightForWidth(self.readConfigurationButton.sizePolicy().hasHeightForWidth())
        self.readConfigurationButton.setSizePolicy(sizePolicy)
        self.readConfigurationButton.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.readConfigurationButton.setText(u"Read Current Controller Configuration")

        self.configurationButtonsGridLayout.addWidget(self.readConfigurationButton, 0, 0, 1, 1)

        self.readAllConfigurationButton = QPushButton(ConfigurationButtons)
        self.readAllConfigurationButton.setObjectName(u"readAllConfigurationButton")
        sizePolicy.setHeightForWidth(self.readAllConfigurationButton.sizePolicy().hasHeightForWidth())
        self.readAllConfigurationButton.setSizePolicy(sizePolicy)
        self.readAllConfigurationButton.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.readAllConfigurationButton.setText(u"Read All Configuration")

        self.configurationButtonsGridLayout.addWidget(self.readAllConfigurationButton, 2, 0, 1, 1)

        self.writeAllChangesButton = QPushButton(ConfigurationButtons)
        self.writeAllChangesButton.setObjectName(u"writeAllChangesButton")
        sizePolicy.setHeightForWidth(self.writeAllChangesButton.sizePolicy().hasHeightForWidth())
        self.writeAllChangesButton.setSizePolicy(sizePolicy)
        self.writeAllChangesButton.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.writeAllChangesButton.setText(u"Write All Changes")

        self.configurationButtonsGridLayout.addWidget(self.writeAllChangesButton, 2, 1, 1, 1)


        self.gridLayout.addLayout(self.configurationButtonsGridLayout, 0, 0, 1, 1)


        self.retranslateUi(ConfigurationButtons)

        QMetaObject.connectSlotsByName(ConfigurationButtons)
    # setupUi

    def retranslateUi(self, ConfigurationButtons):
        ConfigurationButtons.setWindowTitle(QCoreApplication.translate("ConfigurationButtons", u"Form", None))
    # retranslateUi

