# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'recordingMBWEhB.ui'
##
## Created by: Qt User Interface Compiler version 5.14.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide2.QtCore import (QCoreApplication, QDate, QDateTime, QMetaObject,
    QObject, QPoint, QRect, QSize, QTime, QUrl, Qt)
from PySide2.QtGui import (QBrush, QColor, QConicalGradient, QCursor, QFont,
    QFontDatabase, QIcon, QKeySequence, QLinearGradient, QPalette, QPainter,
    QPixmap, QRadialGradient)
from PySide2.QtWidgets import *


class Ui_Dialog(object):
    def setupUi(self, Dialog):
        if not Dialog.objectName():
            Dialog.setObjectName(u"Dialog")
        Dialog.resize(378, 331)
        self.Group = QGroupBox(Dialog)
        self.Group.setObjectName(u"Group")
        self.Group.setGeometry(QRect(10, 10, 231, 311))
        self.name = QLineEdit(self.Group)
        self.name.setObjectName(u"name")
        self.name.setGeometry(QRect(10, 40, 211, 20))
        self.label_8 = QLabel(self.Group)
        self.label_8.setObjectName(u"label_8")
        self.label_8.setGeometry(QRect(10, 20, 76, 13))
        self.addToActions = QPushButton(self.Group)
        self.addToActions.setObjectName(u"addToActions")
        self.addToActions.setGeometry(QRect(10, 280, 100, 23))
        self.start = QPushButton(self.Group)
        self.start.setObjectName(u"start")
        self.start.setGeometry(QRect(10, 250, 101, 23))
        self.preview = QPushButton(self.Group)
        self.preview.setObjectName(u"preview")
        self.preview.setGeometry(QRect(120, 250, 101, 23))
        self.cutSliderLeft = QSlider(self.Group)
        self.cutSliderLeft.setObjectName(u"cutSliderLeft")
        self.cutSliderLeft.setGeometry(QRect(10, 140, 101, 22))
        self.cutSliderLeft.setMinimum(0)
        self.cutSliderLeft.setMaximum(500)
        self.cutSliderLeft.setValue(0)
        self.cutSliderLeft.setOrientation(Qt.Horizontal)
        self.cutSliderRight = QSlider(self.Group)
        self.cutSliderRight.setObjectName(u"cutSliderRight")
        self.cutSliderRight.setGeometry(QRect(110, 140, 111, 22))
        self.cutSliderRight.setMinimum(0)
        self.cutSliderRight.setMaximum(500)
        self.cutSliderRight.setValue(0)
        self.cutSliderRight.setOrientation(Qt.Horizontal)
        self.cutSliderRight.setInvertedAppearance(True)
        self.label_10 = QLabel(self.Group)
        self.label_10.setObjectName(u"label_10")
        self.label_10.setGeometry(QRect(60, 120, 111, 16))
        self.timeBase = QLineEdit(self.Group)
        self.timeBase.setObjectName(u"timeBase")
        self.timeBase.setGeometry(QRect(10, 90, 113, 20))
        self.timeBase.setReadOnly(True)
        self.label_11 = QLabel(self.Group)
        self.label_11.setObjectName(u"label_11")
        self.label_11.setGeometry(QRect(10, 70, 99, 13))
        self.timeFinal = QLineEdit(self.Group)
        self.timeFinal.setObjectName(u"timeFinal")
        self.timeFinal.setGeometry(QRect(60, 220, 131, 20))
        self.timeFinal.setReadOnly(True)
        self.label_12 = QLabel(self.Group)
        self.label_12.setObjectName(u"label_12")
        self.label_12.setGeometry(QRect(50, 200, 142, 13))
        self.cutTimeLeft = QDoubleSpinBox(self.Group)
        self.cutTimeLeft.setObjectName(u"cutTimeLeft")
        self.cutTimeLeft.setGeometry(QRect(10, 170, 62, 22))
        self.cutTimeLeft.setSingleStep(0.100000000000000)
        self.cutTimeRight = QDoubleSpinBox(self.Group)
        self.cutTimeRight.setObjectName(u"cutTimeRight")
        self.cutTimeRight.setGeometry(QRect(160, 170, 62, 22))
        self.cutTimeRight.setSingleStep(0.100000000000000)
        self.replaySpeed = QDoubleSpinBox(self.Group)
        self.replaySpeed.setObjectName(u"replaySpeed")
        self.replaySpeed.setGeometry(QRect(160, 90, 62, 22))
        self.replaySpeed.setMinimum(0.000000000000000)
        self.replaySpeed.setMaximum(10000.000000000000000)
        self.replaySpeed.setValue(1.000000000000000)
        self.label_14 = QLabel(self.Group)
        self.label_14.setObjectName(u"label_14")
        self.label_14.setGeometry(QRect(120, 70, 105, 13))
        self.cancel = QPushButton(self.Group)
        self.cancel.setObjectName(u"cancel")
        self.cancel.setGeometry(QRect(120, 280, 101, 23))
        self.whatToInclude = QGroupBox(Dialog)
        self.whatToInclude.setObjectName(u"whatToInclude")
        self.whatToInclude.setGeometry(QRect(250, 10, 121, 161))
        self.verticalLayout = QVBoxLayout(self.whatToInclude)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.includeClicks = QCheckBox(self.whatToInclude)
        self.includeClicks.setObjectName(u"includeClicks")
        self.includeClicks.setChecked(True)

        self.verticalLayout.addWidget(self.includeClicks)

        self.includeMoves = QCheckBox(self.whatToInclude)
        self.includeMoves.setObjectName(u"includeMoves")
        self.includeMoves.setChecked(True)

        self.verticalLayout.addWidget(self.includeMoves)

        self.includeWheel = QCheckBox(self.whatToInclude)
        self.includeWheel.setObjectName(u"includeWheel")
        self.includeWheel.setChecked(True)

        self.verticalLayout.addWidget(self.includeWheel)

        self.includeKeyboard = QCheckBox(self.whatToInclude)
        self.includeKeyboard.setObjectName(u"includeKeyboard")
        self.includeKeyboard.setChecked(True)

        self.verticalLayout.addWidget(self.includeKeyboard)

        self.hotkeys = QGroupBox(Dialog)
        self.hotkeys.setObjectName(u"hotkeys")
        self.hotkeys.setGeometry(QRect(250, 176, 121, 141))
        self.verticalLayout_2 = QVBoxLayout(self.hotkeys)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.label_13 = QLabel(self.hotkeys)
        self.label_13.setObjectName(u"label_13")

        self.verticalLayout_2.addWidget(self.label_13)

        self.recordingHotkey = QKeySequenceEdit(self.hotkeys)
        self.recordingHotkey.setObjectName(u"recordingHotkey")

        self.verticalLayout_2.addWidget(self.recordingHotkey)

        self.label = QLabel(self.hotkeys)
        self.label.setObjectName(u"label")

        self.verticalLayout_2.addWidget(self.label)

        self.previewHotkey = QKeySequenceEdit(self.hotkeys)
        self.previewHotkey.setObjectName(u"previewHotkey")

        self.verticalLayout_2.addWidget(self.previewHotkey)


        self.retranslateUi(Dialog)
        self.cancel.clicked.connect(Dialog.reject)

        QMetaObject.connectSlotsByName(Dialog)
    # setupUi

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(QCoreApplication.translate("Dialog", u"Dialog", None))
        self.Group.setTitle(QCoreApplication.translate("Dialog", u"Kreator nagra\u0144 do u\u017cycia w makrach", None))
        self.label_8.setText(QCoreApplication.translate("Dialog", u"Nazwij nagranie", None))
        self.addToActions.setText(QCoreApplication.translate("Dialog", u"Dodaj do czynno\u015bci", None))
        self.start.setText(QCoreApplication.translate("Dialog", u"Nagraj", None))
        self.preview.setText(QCoreApplication.translate("Dialog", u"Odtw\u00f3rz", None))
        self.label_10.setText(QCoreApplication.translate("Dialog", u"Przycinanie nagrania", None))
        self.label_11.setText(QCoreApplication.translate("Dialog", u"D\u0142ugo\u015b\u0107 nagrania (s)", None))
        self.label_12.setText(QCoreApplication.translate("Dialog", u"Finalna d\u0142ugo\u015b\u0107 nagrania (s)", None))
        self.label_14.setText(QCoreApplication.translate("Dialog", u"Pr\u0119dko\u015b\u0107 odtwarzania", None))
        self.cancel.setText(QCoreApplication.translate("Dialog", u"Anuluj", None))
        self.whatToInclude.setTitle(QCoreApplication.translate("Dialog", u"Co odtwarza\u0107", None))
        self.includeClicks.setText(QCoreApplication.translate("Dialog", u"Klikni\u0119cia", None))
        self.includeMoves.setText(QCoreApplication.translate("Dialog", u"Ruch myszy", None))
        self.includeWheel.setText(QCoreApplication.translate("Dialog", u"Ruch scrolla", None))
        self.includeKeyboard.setText(QCoreApplication.translate("Dialog", u"Klawisze", None))
        self.hotkeys.setTitle(QCoreApplication.translate("Dialog", u"Skr\u00f3ty klawiszowe", None))
        self.label_13.setText(QCoreApplication.translate("Dialog", u"Skr\u00f3t do nagrywania", None))
        self.recordingHotkey.setKeySequence(QCoreApplication.translate("Dialog", u"Ctrl+R", None))
        self.label.setText(QCoreApplication.translate("Dialog", u"Skr\u00f3t do podgl\u0105du", None))
        self.previewHotkey.setKeySequence(QCoreApplication.translate("Dialog", u"Ctrl+P", None))
    # retranslateUi

