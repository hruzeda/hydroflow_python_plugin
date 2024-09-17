from PyQt5.QtCore import Qt
from qgis.PyQt import QtWidgets

from .classificator import Classificator
from .frmlog import FrmLog
from .params import Params
from .utils.message import Message
from .utils.shp_feature_set_dao import SHPFeatureSetDAO


class Controller:
    def __init__(self, params: Params):
        self.params = params

    def validateFile(self, fileName: str, baseName: str, shapeType: int) -> bool:
        return (
            SHPFeatureSetDAO(self.params.toleranceXY).loadFeatureSet(
                fileName, baseName, shapeType
            )
            is not None
        )

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
                (
                    "Exutório da bacia hidrográfica não identificado ou não "
                    "conectado corretamente à rede de drenagem!"
                ),
            )
        else:  # Houve erro listado no log!
            QtWidgets.QMessageBox.warning(
                self.params.origin,
                "Atenção",
                "Processamento não concluído - leia o log para detalhes!",
            )

    def classifyWaterBasin(self, params: Params) -> int:
        """
        Códigos de erro:
        0 - Processamento concluído com sucesso!
        1 - Processamento concluído com alertas!
        2 - Foz da bacia hidrográfica não identificada!
        3 - Foi identificada mais de uma foz na bacia hidrográfica! (listado no log)
        4 - Foi identificado uma feição com mais de dois afluentes! (listado no log)
        5 - Relações topológicas inesperadas! (listado no log)
        """

        self.params = params
        log = Message(params)

        # Lendo os arquivos de dados.
        params.origin.setCursor(Qt.WaitCursor)
        dao = SHPFeatureSetDAO(params.toleranceXY)

        drainage = dao.loadFeatureSet(params.drainageFileName, "drenagem", 0)
        boundary = dao.loadFeatureSet(params.boundaryFileName, "limite", 1)

        if not drainage:
            params.origin.setCursor(Qt.ArrowCursor)
            return 2

        if not boundary:
            params.origin.setCursor(Qt.ArrowCursor)
            return 3

        # Classificando a bacia.
        classificator = Classificator(drainage, boundary, params, log)

        result = classificator.classifyWaterBasin()
        params.origin.setCursor(Qt.ArrowCursor)
        self.displayMessage(result)

        # Salvando o novo arquivo.
        if result in (0, 1):
            # Obtendo nome do novo arquivo.
            new = QtWidgets.QFileDialog.getSaveFileName(
                params.origin,
                "Salvar bacia classificada como",
                "",
                "Shape File(*.shp)",
            )[0]
            if new != "":
                params.origin.setCursor(Qt.WaitCursor)
                params.newFileName = new
                log.result = new

                # Gravando os arquivos.
                dao.saveFeatureSet(drainage, params, log)

                topology_log = open(new.replace(".shp", "_topo.txt"), "w")
                for relation in classificator.topologicalRelations.mouths:
                    topology_log.write(
                        f"{relation.source.featureId};{relation.destination.featureId}\n"
                    )
                for relation in classificator.topologicalRelations.items:
                    topology_log.write(
                        f"{relation.source.featureId};{relation.destination.featureId}\n"
                    )
                topology_log.close()

                params.origin.setCursor(Qt.ArrowCursor)

            result = 0
        else:
            result = 9

        # Verificando se há mensagens no log.
        if log.hasMessages():
            formLog = FrmLog(params.origin, log)
            formLog.show()
            formLog.displayLog()

        return result
