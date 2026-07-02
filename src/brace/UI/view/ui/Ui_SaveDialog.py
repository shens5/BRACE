# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'saveDialogXbjldk.ui'
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
from PySide6.QtWidgets import (QAbstractButton, QApplication, QDialog, QDialogButtonBox,
    QFrame, QGridLayout, QLabel, QSizePolicy,
    QWidget)
import brace.UI.view.resourceFile_rc

class Ui_SaveDialog(object):
    def setupUi(self, SaveDialog):
        if not SaveDialog.objectName():
            SaveDialog.setObjectName(u"SaveDialog")
        SaveDialog.setWindowModality(Qt.WindowModality.NonModal)
        SaveDialog.resize(720, 220)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(SaveDialog.sizePolicy().hasHeightForWidth())
        SaveDialog.setSizePolicy(sizePolicy)
        icon = QIcon(QIcon.fromTheme(QIcon.ThemeIcon.DocumentSave))
        SaveDialog.setWindowIcon(icon)
        SaveDialog.setAutoFillBackground(False)
        SaveDialog.setSizeGripEnabled(True)
        SaveDialog.setModal(True)
        self.saveDialogGridLayout = QGridLayout(SaveDialog)
        self.saveDialogGridLayout.setObjectName(u"saveDialogGridLayout")
        self.saveDialogGridLayout.setContentsMargins(60, 30, 30, -1)
        self.saveDialogImage = QLabel(SaveDialog)
        self.saveDialogImage.setObjectName(u"saveDialogImage")
        self.saveDialogImage.setMaximumSize(QSize(100, 100))
        self.saveDialogImage.setPixmap(QPixmap(u"../icons/save-svgrepo.svg"))
        self.saveDialogImage.setScaledContents(True)

        self.saveDialogGridLayout.addWidget(self.saveDialogImage, 0, 0, 1, 1)

        self.saveDialogTextLabel = QLabel(SaveDialog)
        self.saveDialogTextLabel.setObjectName(u"saveDialogTextLabel")
        sizePolicy.setHeightForWidth(self.saveDialogTextLabel.sizePolicy().hasHeightForWidth())
        self.saveDialogTextLabel.setSizePolicy(sizePolicy)
        font = QFont()
        font.setPointSize(9)
        self.saveDialogTextLabel.setFont(font)
        self.saveDialogTextLabel.setFrameShape(QFrame.Shape.NoFrame)
        self.saveDialogTextLabel.setFrameShadow(QFrame.Shadow.Plain)
        self.saveDialogTextLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.saveDialogTextLabel.setWordWrap(True)
        self.saveDialogTextLabel.setMargin(0)

        self.saveDialogGridLayout.addWidget(self.saveDialogTextLabel, 0, 1, 1, 1)

        self.saveDialogButtonBox = QDialogButtonBox(SaveDialog)
        self.saveDialogButtonBox.setObjectName(u"saveDialogButtonBox")
        self.saveDialogButtonBox.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.saveDialogButtonBox.setOrientation(Qt.Orientation.Horizontal)
        self.saveDialogButtonBox.setStandardButtons(QDialogButtonBox.StandardButton.No|QDialogButtonBox.StandardButton.Yes)

        self.saveDialogGridLayout.addWidget(self.saveDialogButtonBox, 1, 1, 1, 1)


        self.retranslateUi(SaveDialog)
        self.saveDialogButtonBox.accepted.connect(SaveDialog.accept)
        self.saveDialogButtonBox.rejected.connect(SaveDialog.reject)

        QMetaObject.connectSlotsByName(SaveDialog)
    # setupUi

    def retranslateUi(self, SaveDialog):
        SaveDialog.setWindowTitle(QCoreApplication.translate("SaveDialog", u"Save Streamed Data", None))
        self.saveDialogImage.setText("")
        self.saveDialogTextLabel.setText(QCoreApplication.translate("SaveDialog", u"Save most recent streamed data?", None))
    # retranslateUi

