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

from PyQt5 import QtCore
from qgis.PyQt import QtWidgets

from .controller import Controller
from .hydroflow_dialog_base_ui import Ui_HydroflowDialogBase
from .params import Params


class HydroflowDialog(QtWidgets.QDialog, Ui_HydroflowDialogBase):
    def __init__(self, parent=None):
        """Constructor."""
        super(HydroflowDialog).__init__(parent)
        # Set up the user interface from Designer through FORM_CLASS.
        # After self.setupUi() you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)

    def get_path(self, titulo):
        return QtWidgets.QFileDialog.getOpenFileName(
            self, titulo, "", "Shape File(*.shp)"
        )

    def on_pushButton_HidLn_clicked(self):
        self.lineEdit_HidLn.setText(self.get_path("Arquivo da rede de drenagem"))

    def on_pushButton_Lim_clicked(self):
        self.lineEdit_Lim.setText(self.get_path("Arquivo da rede de drenagem"))

    def on_comboBox_currentIndexChanged(self, index):
        if index == 0:
            self.lineEdit_TolXY.setText("0.001")
        elif index == 1:
            self.lineEdit_TolXY.setText("0.000001")
        elif index == 2:
            self.lineEdit_TolXY.setText("0.03937")
        elif index == 3:
            self.lineEdit_TolXY.setText("0.001")

    def on_checkBox_FlowOnly_stateChanged(self, CBState):
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

    def avaliarInferencia(self):
        if (
            not self.checkBox_Strahler.isChecked()
            and not self.checkBox_Shreve.isChecked()
        ):
            self.checkBox_FlowOnly.setChecked(True)

    def on_pushButton_Close_clicked(self):
        QtCore.QCoreApplication.instance().exit(0)

    def on_checkBox_Strahler_clicked(self):
        self.avaliarInferencia()

    def on_checkBox_Shreve_clicked(self):
        if not self.checkBox_Shreve.isChecked():
            self.avaliarInferencia()

    def on_pushButton_Exec_clicked(self):
        try:
            nomeBacia = self.lineEdit_HidLn.text()
            nomeLimite = self.lineEdit_Lim.text()

            # Validando a tolerância.
            if self.lineEdit_TolXY.text().isEmpty():
                self.lineEdit_TolXY.setText("0")

            try:
                tol = float(self.lineEdit_TolXY.text())
            except ValueError:
                tol = -1

            if tol < 0:
                self.exibirMensagem(4)
                return

            # Validando arquivos.
            # Determinando o tipo de classificação Strahler.
            tipoClassificacaoStrahler = 0

            # A opção de classificação Strahler relaxada não está disponível
            # no formulário (tipoClassificacaoStrahler = 2).
            tipoClassificacaoStrahler = 0
            if self.checkBox_Strahler.isChecked():
                tipoClassificacaoStrahler = 1

            params = Params(
                self,
                nomeBacia,
                nomeLimite,
                tol,
                tipoClassificacaoStrahler,
                self.checkBox_Shreve.isChecked(),
            )

            con = Controller(params)

            if not con.validateFile(nomeBacia, "drenagem"):
                self.exibirMensagem(2)
                return

            if not con.validateFile(nomeLimite, "limite"):
                self.exibirMensagem(3)
                return

            # Iniciando o processo.
            resultado = con.classifyWaterBasin(params)
            self.exibirMensagem(resultado)  # Valores para resultado: 0, 2, 3 ou 9.
        except Exception as e:
            print(e)
            self.exibirMensagem(5)

    def exibirMensagem(self, codigo):
        """
        Códigos:
        0 - SEM MENSAGEM.
        1 - Os dois arquivos de entrada são iguais!
        2 - Arquivo da rede de drenagem inválido ou não pode ser acessado!
        3 - Arquivo do limite da bacia/exutório inválido ou não pode ser acessado!
        4 - O valor da Tolerância XY não pode ser negativo!
        """
        title = "Atenção"
        if codigo == 1:
            QtWidgets.QMessageBox.warning(
                self, title, "Os dois arquivos de entrada são iguais!"
            )
        elif codigo == 2:
            QtWidgets.QMessageBox.warning(
                self,
                title,
                "Arquivo da rede de drenagem inválido ou não pode ser acessado!",
            )
        elif codigo == 3:
            QtWidgets.QMessageBox.warning(
                self,
                title,
                (
                    "Arquivo do limite da bacia/exutório inválido ou "
                    "não pode ser acessado!"
                ),
            )
        elif codigo == 4:
            QtWidgets.QMessageBox.warning(
                self, title, "O valor da Tolerância XY não pode ser negativo!"
            )
        elif codigo == 5:
            QtWidgets.QMessageBox.warning(
                self,
                title,
                "Houve um erro inesperado. O processamento foi interrompido!",
            )
