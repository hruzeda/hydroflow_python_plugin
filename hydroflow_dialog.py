# -*- coding: utf-8 -*-
"""
/***************************************************************************
 HydroflowDialog
                                 A QGIS plugin
 Compute drainage orders in drainage basins using Strahler and Shreve methods
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                             -------------------
        begin                : 2024-08-07
        git sha              : $Format:%H$
        copyright            : (C) 2024 by Henrique Uzêda
        email                : hruzeda@gmail.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

import traceback
from decimal import Decimal
from typing import Any

from PyQt5 import QtWidgets
from PyQt5.QtCore import pyqtSlot
from qgis.core import Qgis, QgsMessageLog

from .controller import Controller
from .hydroflow_dialog_base_ui import Ui_HydroflowDialogBase
from .params import Params


class HydroflowDialog(QtWidgets.QDialog, Ui_HydroflowDialogBase):
    def __init__(self, parent: Any = None) -> None:
        """Constructor."""
        super(HydroflowDialog, self).__init__(parent)  # pylint: disable=super-with-arguments,too-many-function-args
        # Set up the user interface from Designer through FORM_CLASS.
        # After self.setupUi() you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)

    def get_path(self, titulo: str) -> Any:
        return QtWidgets.QFileDialog.getOpenFileName(
            self, titulo, "", "Shape File (*.shp)"
        )[0]

    @pyqtSlot()
    def on_pushButton_HidLn_clicked(self) -> None:
        path = self.get_path("Arquivo da rede de drenagem")
        if path:
            self.lineEdit_HidLn.setText(str(path))

    @pyqtSlot()
    def on_pushButton_Lim_clicked(self) -> None:
        path = self.get_path("Arquivo da rede de drenagem")
        if path:
            self.lineEdit_Lim.setText(path)

    @pyqtSlot()
    def on_comboBox_currentIndexChanged(self, index: int) -> None:
        if index == 0:
            self.lineEdit_TolXY.setText("0.001")
        elif index == 1:
            self.lineEdit_TolXY.setText("0.000001")
        elif index == 2:
            self.lineEdit_TolXY.setText("0.03937")
        elif index == 3:
            self.lineEdit_TolXY.setText("0.001")

    @pyqtSlot()
    def on_checkBox_FlowOnly_stateChanged(self, CBState: str) -> None:
        if CBState == "checked":
            self.checkBox_Strahler.setChecked(False)
            self.checkBox_Strahler.setEnabled(False)
            self.checkBox_Shreve.setChecked(False)
            self.checkBox_Shreve.setEnabled(False)
        else:
            self.checkBox_Strahler.setEnabled(True)
            self.checkBox_Strahler.setChecked(True)
            self.checkBox_Shreve.setEnabled(True)
            self.checkBox_Shreve.setChecked(True)

    def evaluateInference(self) -> None:
        if (
            not self.checkBox_Strahler.isChecked()
            and not self.checkBox_Shreve.isChecked()
        ):
            self.checkBox_FlowOnly.setChecked(True)

    @pyqtSlot()
    def on_checkBox_Strahler_clicked(self) -> None:
        self.evaluateInference()

    @pyqtSlot()
    def on_checkBox_Shreve_clicked(self) -> None:
        self.evaluateInference()

    @pyqtSlot()
    def on_checkBox_MonitorPoint_clicked(self) -> None:
        self.lineEdit_MonitorPointN.setEnabled(
            self.checkBox_MonitorPoint.isChecked()
        )

    @pyqtSlot()
    def on_pushButton_Exec_clicked(self) -> None:
        try:
            drainageFileName = self.lineEdit_HidLn.text()
            boundaryFileName = self.lineEdit_Lim.text()

            # Validando a tolerância.
            if not self.lineEdit_TolXY.text():
                self.lineEdit_TolXY.setText("0")

            try:
                tolerance = Decimal(self.lineEdit_TolXY.text())
            except ValueError:
                tolerance = Decimal(-1)

            if tolerance < 0:
                self.displayMessage(4)
                return

            # Validando arquivos.
            # Determinando o tipo de classificação Strahler.
            strahlerClassificationType = 0

            # A opção de classificação Strahler relaxada não está disponível
            # no formulário (tipoClassificacaoStrahler = 2).
            strahlerClassificationType = 0
            if self.checkBox_Strahler.isChecked():
                strahlerClassificationType = 1

            params = Params(
                origin=self,
                drainageFileName=drainageFileName,
                boundaryFileName=boundaryFileName,
                toleranceXY=tolerance,
                strahlerOrderType=strahlerClassificationType,
                shreveOrderEnabled=self.checkBox_Shreve.isChecked(),
                monitorPointEnabled=self.checkBox_MonitorPoint.isChecked(),
                monitorPointN=int(self.lineEdit_MonitorPointN.text() or 5),
            )

            con = Controller(params)

            if not con.validateFile(drainageFileName, "drenagem", 0):
                self.displayMessage(2)
                return

            if not con.validateFile(boundaryFileName, "limite", 1):
                self.displayMessage(3)
                return

            # Iniciando o processo.
            resultado = con.classifyWaterBasin(params)
            self.displayMessage(resultado)  # Valores para resultado: 0, 2, 3 ou 9.
        except Exception:  # pylint: disable=broad-exception-caught
            QgsMessageLog.logMessage(
                traceback.format_exc(), "Hydroflow", Qgis.MessageLevel.Critical, True
            )
            self.displayMessage(5)

    def displayMessage(self, error_code: int) -> None:
        """
        Códigos:
        0 - SEM MENSAGEM.
        1 - Os dois arquivos de entrada são iguais!
        2 - Arquivo da rede de drenagem inválido ou não pode ser acessado!
        3 - Arquivo do limite da bacia/exutório inválido ou não pode ser acessado!
        4 - O valor da Tolerância XY não pode ser negativo!
        """
        title = "Atenção"
        if error_code == 1:
            QtWidgets.QMessageBox.warning(
                self, title, "Os dois arquivos de entrada são iguais!"
            )
        elif error_code == 2:
            QtWidgets.QMessageBox.warning(
                self,
                title,
                "Arquivo da rede de drenagem inválido ou não pode ser acessado!",
            )
        elif error_code == 3:
            QtWidgets.QMessageBox.warning(
                self,
                title,
                (
                    "Arquivo do limite da bacia/exutório inválido ou "
                    "não pode ser acessado!"
                ),
            )
        elif error_code == 4:
            QtWidgets.QMessageBox.warning(
                self, title, "O valor da Tolerância XY não pode ser negativo!"
            )
        elif error_code == 5:
            QtWidgets.QMessageBox.warning(
                self,
                title,
                "Houve um erro inesperado. O processamento foi interrompido!",
            )
