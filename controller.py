from PyQt5.QtCore import Qt
from qgis.PyQt import QtWidgets

from classificator import Classificator
from models.params import Params
from models.shp_feature_set_dao import SHPFeatureSetDAO
from utils.message import Message


class Controller:
    def __init__(self, params: Params):
        self.params = params

    def validateFile(self, fileName: str, baseName: str) -> bool:
        return SHPFeatureSetDAO().loadFeatureSet(fileName, baseName) is not None

    def displayMessage(self, result: int) -> None:
        if result == 0:
            QtWidgets.QMessageBox.about(
                self.params.origin, "Aviso", "Processamento concluído com sucesso!"
            )
        elif result == 1:
            QtWidgets.QMessageBox.about(
                self.params.origin,
                "Aviso",
                "Processamento concluído com alertas - leia o log para detalhes!",
            )
        elif result == 2:
            QtWidgets.QMessageBox.warning(
                self.params.origin,
                "Atenção",
                "Exutório da bacia hidrográfica não identificado ou não conectado corretamente à rede de drenagem!",
            )
        else:  # Houve erro listado no log!
            QtWidgets.QMessageBox.warning(
                self.params.origin,
                "Atenção",
                "Processamento não concluído - leia o log para detalhes!",
            )

    def classifyWaterBasin(self, params: Params) -> int:
        self.params = params
        log = Message(params)

        # Lendo os arquivos de dados.
        params.origin.setCursor(Qt.WaitCursor)
        dao = SHPFeatureSetDAO(params.toleranceXY)

        basin = dao.loadFeatureSet(params.basinFileName, "hidrografia", 0)
        boundary = dao.loadFeatureSet(params.boundaryFileName, "limite", 1)

        if not basin:
            params.origin.setCursor(Qt.ArrowCursor)
            return 2

        if not boundary:
            params.origin.setCursor(Qt.ArrowCursor)
            return 3

        # Classificando a bacia.
        classificator = Classificator(basin, boundary, params, log)

        """
        Códigos de erro:
        0 - Processamento concluído com sucesso!
        1 - Processamento concluído com alertas!
        2 - Foz da bacia hidrográfica não identificada!
        3 - Foi identificada mais de uma foz na bacia hidrográfica! (listado no log)
        4 - Foi identificado uma feição com mais de dois afluentes! (listado no log)
        5 - Relações topológicas inesperadas! (listado no log)
        """
        result = classificator.classifyWaterBasin()
        params.origin.setCursor(Qt.ArrowCursor)
        self.displayMessage(result)

        # Salvando o novo arquivo.
        if result == 0 or result == 1:
            # Obtendo nome do novo arquivo.
            new = QtWidgets.QFileDialog.getSaveFileName(
                params.origin, "Salvar bacia classificada como", "", "Shape File(*.shp)"
            )
            if new != "":
                params.origin.setCursor(Qt.WaitCursor)
                params.setNomeNovoArquivo(new)
                log.result = new

                # Gravando os arquivos.
                dao.saveFeatureSet(basin, params)
                params.origin.setCursor(Qt.ArrowCursor)
            result = 0
        else:
            result = 9

        # Verificando se há mensagens no log.
        # if log.hasMessages():
        # formLog = FrmLog(params.origem, log)
        # formLog.exibirLog()

        # Apagando os objetos.
        classificator.limparHydroflow()
        boundary.LimparConjuntoFeicao()
        basin.LimparConjuntoFeicao()

        return result