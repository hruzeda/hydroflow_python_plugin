# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'hydroflow_dialog_base.ui'
#
# Created by: PyQt5 UI code generator 5.15.11
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_HydroflowDialogBase(object):
    def __init__(self) -> None:
        self.groupBox: QtWidgets.QGroupBox
        self.groupBox_Lim: QtWidgets.QGroupBox
        self.groupBox_HidLn: QtWidgets.QGroupBox

        self.lineEdit_Lim: QtWidgets.QLineEdit
        self.lineEdit_HidLn: QtWidgets.QLineEdit
        self.lineEdit_MonitorPointN: QtWidgets.QLineEdit
        self.lineEdit_TolXY: QtWidgets.QLineEdit

        self.label_2: QtWidgets.QLabel
        self.label_3: QtWidgets.QLabel
        self.label_4: QtWidgets.QLabel

        self.checkBox_Strahler: QtWidgets.QCheckBox
        self.checkBox_Shreve: QtWidgets.QCheckBox
        self.checkBox_FlowOnly: QtWidgets.QCheckBox
        self.checkBox_MonitorPoint: QtWidgets.QCheckBox

        self.pushButton_Lim: QtWidgets.QPushButton
        self.pushButton_HidLn: QtWidgets.QPushButton
        self.pushButton_Exec: QtWidgets.QPushButton

    def setupUi(self, HydroflowDialogBase: QtWidgets.QDialog) -> None:
        HydroflowDialogBase.setObjectName("HydroflowDialogBase")
        HydroflowDialogBase.resize(563, 316)
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed
        )
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(
            HydroflowDialogBase.sizePolicy().hasHeightForWidth()
        )
        HydroflowDialogBase.setSizePolicy(sizePolicy)
        icon = QtGui.QIcon()
        icon.addPixmap(
            QtGui.QPixmap(":hydroflow.ico"), QtGui.QIcon.Normal, QtGui.QIcon.Off
        )
        HydroflowDialogBase.setWindowIcon(icon)
        HydroflowDialogBase.setAutoFillBackground(True)
        self.pushButton_Exec = QtWidgets.QPushButton(HydroflowDialogBase)
        self.pushButton_Exec.setGeometry(QtCore.QRect(450, 272, 88, 28))
        font = QtGui.QFont()
        font.setBold(True)
        self.pushButton_Exec.setFont(font)
        self.pushButton_Exec.setObjectName("pushButton_Exec")
        self.groupBox_Lim = QtWidgets.QGroupBox(HydroflowDialogBase)
        self.groupBox_Lim.setGeometry(QtCore.QRect(286, 10, 264, 61))
        font = QtGui.QFont()
        font.setBold(True)
        self.groupBox_Lim.setFont(font)
        self.groupBox_Lim.setAutoFillBackground(False)
        self.groupBox_Lim.setStyleSheet("QGroupBox { border: 1px solid #575859; }")
        self.groupBox_Lim.setObjectName("groupBox_Lim")
        self.lineEdit_Lim = QtWidgets.QLineEdit(self.groupBox_Lim)
        self.lineEdit_Lim.setEnabled(False)
        self.lineEdit_Lim.setGeometry(QtCore.QRect(10, 27, 205, 26))
        self.lineEdit_Lim.setObjectName("lineEdit_Lim")
        self.pushButton_Lim = QtWidgets.QPushButton(self.groupBox_Lim)
        self.pushButton_Lim.setGeometry(QtCore.QRect(224, 26, 30, 28))
        self.pushButton_Lim.setText("")
        icon1 = QtGui.QIcon()
        icon1.addPixmap(
            QtGui.QPixmap(":search.ico"), QtGui.QIcon.Normal, QtGui.QIcon.Off
        )
        self.pushButton_Lim.setIcon(icon1)
        self.pushButton_Lim.setObjectName("pushButton_Lim")
        self.groupBox = QtWidgets.QGroupBox(HydroflowDialogBase)
        self.groupBox.setGeometry(QtCore.QRect(10, 82, 541, 177))
        font = QtGui.QFont()
        font.setBold(True)
        self.groupBox.setFont(font)
        self.groupBox.setAutoFillBackground(False)
        self.groupBox.setStyleSheet("QGroupBox { border: 1px solid #575859; }")
        self.groupBox.setFlat(False)
        self.groupBox.setCheckable(False)
        self.groupBox.setObjectName("groupBox")
        self.label_2 = QtWidgets.QLabel(self.groupBox)
        self.label_2.setGeometry(QtCore.QRect(10, 120, 111, 16))
        self.label_2.setAlignment(QtCore.Qt.AlignLeft)
        self.label_2.setObjectName("label_2")
        self.lineEdit_TolXY = QtWidgets.QLineEdit(self.groupBox)
        self.lineEdit_TolXY.setGeometry(QtCore.QRect(10, 140, 161, 26))
        self.lineEdit_TolXY.setText("0.001")
        self.lineEdit_TolXY.setAlignment(QtCore.Qt.AlignLeft)
        self.lineEdit_TolXY.setObjectName("lineEdit_TolXY")
        self.checkBox_FlowOnly = QtWidgets.QCheckBox(self.groupBox)
        self.checkBox_FlowOnly.setGeometry(QtCore.QRect(10, 96, 131, 18))
        self.checkBox_FlowOnly.setObjectName("checkBox_FlowOnly")
        self.label_3 = QtWidgets.QLabel(self.groupBox)
        self.label_3.setGeometry(QtCore.QRect(10, 25, 51, 16))
        self.label_3.setObjectName("label_3")
        self.checkBox_Strahler = QtWidgets.QCheckBox(self.groupBox)
        self.checkBox_Strahler.setGeometry(QtCore.QRect(10, 45, 151, 18))
        self.checkBox_Strahler.setChecked(True)
        self.checkBox_Strahler.setObjectName("checkBox_Strahler")
        self.checkBox_Shreve = QtWidgets.QCheckBox(self.groupBox)
        self.checkBox_Shreve.setGeometry(QtCore.QRect(10, 70, 131, 18))
        self.checkBox_Shreve.setChecked(True)
        self.checkBox_Shreve.setObjectName("checkBox_Shreve")
        self.checkBox_MonitorPoint = QtWidgets.QCheckBox(self.groupBox)
        self.checkBox_MonitorPoint.setGeometry(QtCore.QRect(282, 40, 260, 20))
        self.checkBox_MonitorPoint.setObjectName("checkBox_MonitorPoint")
        self.label_4 = QtWidgets.QLabel(self.groupBox)
        self.label_4.setGeometry(QtCore.QRect(240, 70, 281, 20))
        self.label_4.setAlignment(QtCore.Qt.AlignRight)
        self.label_4.setObjectName("label_4")
        self.lineEdit_MonitorPointN = QtWidgets.QLineEdit(self.groupBox)
        self.lineEdit_MonitorPointN.setEnabled(False)
        self.lineEdit_MonitorPointN.setGeometry(QtCore.QRect(320, 94, 201, 26))
        self.lineEdit_MonitorPointN.setText("5")
        self.lineEdit_MonitorPointN.setObjectName("lineEdit_MonitorPointN")
        self.groupBox_HidLn = QtWidgets.QGroupBox(HydroflowDialogBase)
        self.groupBox_HidLn.setGeometry(QtCore.QRect(10, 10, 264, 61))
        font = QtGui.QFont()
        font.setBold(True)
        self.groupBox_HidLn.setFont(font)
        self.groupBox_HidLn.setAutoFillBackground(False)
        self.groupBox_HidLn.setStyleSheet("QGroupBox { border: 1px solid #575859; }")
        self.groupBox_HidLn.setFlat(False)
        self.groupBox_HidLn.setObjectName("groupBox_HidLn")
        self.lineEdit_HidLn = QtWidgets.QLineEdit(self.groupBox_HidLn)
        self.lineEdit_HidLn.setEnabled(False)
        self.lineEdit_HidLn.setGeometry(QtCore.QRect(10, 27, 205, 26))
        self.lineEdit_HidLn.setObjectName("lineEdit_HidLn")
        self.pushButton_HidLn = QtWidgets.QPushButton(self.groupBox_HidLn)
        self.pushButton_HidLn.setGeometry(QtCore.QRect(224, 26, 30, 28))
        self.pushButton_HidLn.setText("")
        self.pushButton_HidLn.setIcon(icon1)
        self.pushButton_HidLn.setObjectName("pushButton_HidLn")

        self.retranslateUi(HydroflowDialogBase)
        QtCore.QMetaObject.connectSlotsByName(HydroflowDialogBase)

    def retranslateUi(self, HydroflowDialogBase: QtWidgets.QDialog) -> None:
        _translate = QtCore.QCoreApplication.translate
        HydroflowDialogBase.setWindowTitle(
            _translate("HydroflowDialogBase", "Hydroflow")
        )
        self.pushButton_Exec.setText(_translate("HydroflowDialogBase", "Executar"))
        self.groupBox_Lim.setTitle(
            _translate("HydroflowDialogBase", " Limite da área ")
        )
        self.groupBox.setTitle(_translate("HydroflowDialogBase", " Opções "))
        self.label_2.setText(_translate("HydroflowDialogBase", "Tolerância XY:"))
        self.checkBox_FlowOnly.setText(
            _translate("HydroflowDialogBase", "Somente fluxos")
        )
        self.label_3.setText(_translate("HydroflowDialogBase", "Inferir:"))
        self.checkBox_Strahler.setText(
            _translate("HydroflowDialogBase", "Ordens por Strahler")
        )
        self.checkBox_Shreve.setText(
            _translate("HydroflowDialogBase", "Ordens por Shreve")
        )
        self.checkBox_MonitorPoint.setText(
            _translate("HydroflowDialogBase", "Sugerir trechos para monitoramento")
        )
        self.label_4.setText(
            _translate(
                "HydroflowDialogBase", "Quantidade de trechos para monitoramento"
            )
        )
        self.groupBox_HidLn.setTitle(
            _translate("HydroflowDialogBase", " Rede de drenagem ")
        )


from . import resources_rc  # noqa: E402, F401
