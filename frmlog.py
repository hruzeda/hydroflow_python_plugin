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

from typing import Any

from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt, pyqtSlot

from .frmlog_ui import Ui_FrmLog
from .utils.message import Message


class FrmLog(QtWidgets.QDialog, Ui_FrmLog):
    def __init__(self, origin: Any, message: Message) -> None:
        """Constructor."""
        super(FrmLog, self).__init__(origin)  # pylint: disable=super-with-arguments,too-many-function-args
        # Set up the user interface from Designer through FORM_CLASS.
        # After self.setupUi() you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)
        self.origin = origin
        self.message = message

    def displayLog(self) -> None:
        # Opening the form.
        self.pushButton.setEnabled(False)
        self.move((self.origin.x() + 10), (self.origin.y() + 32))

        self.textEdit.append(self.message.getHeader())

        for item in self.message.list:
            self.textEdit.append(item)

        self.textEdit.append(self.message.getFooter())

        self.exec_()

    @pyqtSlot()
    def on_pushButton_2_clicked(self) -> None:
        self.close()

    @pyqtSlot()
    def on_pushButton_clicked(self) -> None:
        logFileName = QtWidgets.QFileDialog.getSaveFileName(
            self, "Salvar arquivo como", "", "(*.txt)"
        )[0]
        try:
            logFile = open(logFileName, "w")
            if logFile:
                logFile.write(self.message.getHeader() + "\n")
                for item in self.message.list:
                    logFile.write(item + "\n")
                logFile.write(self.message.getFooter() + "\n")
        finally:
            logFile.close()

    def list(self, message: str) -> None:
        self.textEdit.append(message)

    def logStopped(self) -> None:
        self.setCursor(Qt.ArrowCursor)
        self.pushButton.setEnabled(True)
