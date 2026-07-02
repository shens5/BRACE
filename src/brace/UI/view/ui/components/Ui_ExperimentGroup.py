# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'experimentGroupgfVJUb.ui'
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
from PySide6.QtWidgets import (QApplication, QFormLayout, QGridLayout, QGroupBox,
    QLabel, QSizePolicy, QSpinBox, QWidget)

class Ui_UBQVisitTrials(object):
    def setupUi(self, UBQVisitTrials):
        if not UBQVisitTrials.objectName():
            UBQVisitTrials.setObjectName(u"UBQVisitTrials")
        UBQVisitTrials.resize(172, 107)
        self.gridLayout = QGridLayout(UBQVisitTrials)
        self.gridLayout.setSpacing(0)
        self.gridLayout.setObjectName(u"gridLayout")
        self.gridLayout.setContentsMargins(0, 0, 0, 0)
        self.experimentGroupBox = QGroupBox(UBQVisitTrials)
        self.experimentGroupBox.setObjectName(u"experimentGroupBox")
        font = QFont()
        font.setPointSize(9)
        self.experimentGroupBox.setFont(font)
        self.experimentFormLayout = QFormLayout(self.experimentGroupBox)
        self.experimentFormLayout.setObjectName(u"experimentFormLayout")
        self.experimentFormLayout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        self.experimentFormLayout.setHorizontalSpacing(0)
        self.experimentFormLayout.setVerticalSpacing(8)
        self.experimentFormLayout.setContentsMargins(2, 2, 2, 2)
        self.ubqLabel = QLabel(self.experimentGroupBox)
        self.ubqLabel.setObjectName(u"ubqLabel")
        self.ubqLabel.setFont(font)

        self.experimentFormLayout.setWidget(0, QFormLayout.ItemRole.LabelRole, self.ubqLabel)

        self.visitLabel = QLabel(self.experimentGroupBox)
        self.visitLabel.setObjectName(u"visitLabel")
        self.visitLabel.setFont(font)

        self.experimentFormLayout.setWidget(1, QFormLayout.ItemRole.LabelRole, self.visitLabel)

        self.visitSpinBox = QSpinBox(self.experimentGroupBox)
        self.visitSpinBox.setObjectName(u"visitSpinBox")
        self.visitSpinBox.setFont(font)
        self.visitSpinBox.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        self.experimentFormLayout.setWidget(1, QFormLayout.ItemRole.FieldRole, self.visitSpinBox)

        self.trialLabel = QLabel(self.experimentGroupBox)
        self.trialLabel.setObjectName(u"trialLabel")
        self.trialLabel.setFont(font)

        self.experimentFormLayout.setWidget(2, QFormLayout.ItemRole.LabelRole, self.trialLabel)

        self.trialSpinBox = QSpinBox(self.experimentGroupBox)
        self.trialSpinBox.setObjectName(u"trialSpinBox")
        self.trialSpinBox.setFont(font)
        self.trialSpinBox.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.trialSpinBox.setValue(1)

        self.experimentFormLayout.setWidget(2, QFormLayout.ItemRole.FieldRole, self.trialSpinBox)

        self.ubqSpinBox = QSpinBox(self.experimentGroupBox)
        self.ubqSpinBox.setObjectName(u"ubqSpinBox")
        self.ubqSpinBox.setFont(font)
        self.ubqSpinBox.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        self.experimentFormLayout.setWidget(0, QFormLayout.ItemRole.FieldRole, self.ubqSpinBox)


        self.gridLayout.addWidget(self.experimentGroupBox, 0, 1, 1, 1)


        self.retranslateUi(UBQVisitTrials)

        QMetaObject.connectSlotsByName(UBQVisitTrials)
    # setupUi

    def retranslateUi(self, UBQVisitTrials):
        UBQVisitTrials.setWindowTitle(QCoreApplication.translate("UBQVisitTrials", u"Form", None))
        self.experimentGroupBox.setTitle(QCoreApplication.translate("UBQVisitTrials", u"Experiment #", None))
        self.ubqLabel.setText(QCoreApplication.translate("UBQVisitTrials", u"UBQ #", None))
        self.visitLabel.setText(QCoreApplication.translate("UBQVisitTrials", u"Visit #", None))
        self.trialLabel.setText(QCoreApplication.translate("UBQVisitTrials", u"Trial #", None))
    # retranslateUi

