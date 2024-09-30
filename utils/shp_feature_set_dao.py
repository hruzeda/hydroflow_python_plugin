import shutil
from pathlib import Path
from typing import Optional

from PyQt5.QtCore import QVariant
from qgis.core import (
    QgsFeature,
    QgsFeatureRequest,
    QgsField,
    QgsFields,
    QgsProject,
    QgsVectorFileWriter,
    QgsVectorLayer,
)

from ..models.attribute import Attribute
from ..models.feature import Feature
from ..models.feature_set import FeatureSet
from ..models.new_feature_attribute import NewFeatureAttributes
from ..models.observation import Observation
from ..models.segment import Segment
from ..models.vertex import Vertex
from ..params import Params
from ..utils.message import Message


class SHPFeatureSetDAO:
    def __init__(self, tolerance: float = 0) -> None:
        self.tolerance = tolerance

    # Tipos: 0 - bacia; 1 - limite.
    def loadFeatureSet(
        self, fileName: str, baseName: str, shapeType: int
    ) -> Optional[FeatureSet]:
        # Lendo o registro
        layer = QgsVectorLayer(fileName, baseName, "ogr")
        if not layer.isValid():
            print("Failed to load layer!")
            return None

        # Initialize variables
        obs = Observation()
        featureSet = FeatureSet(shapeType, fileName, layer.wkbType(), obs, layer)

        msg_1 = "Feição com partes multiplas. Veja: "
        msg_2 = "Parte da feição FID "
        msg_3 = "Feição não processada."

        # Montando as feições
        newFeatureId = layer.featureCount()
        for featureId, qgsFeature in enumerate(layer.getFeatures()):
            geometry = qgsFeature.geometry()
            if geometry.isMultipart():
                # Lendo as partes.
                vertexId = 0
                partsIterator = geometry.parts()
                for partId, part in enumerate(partsIterator):
                    newFeature = partId > 0
                    feature = Feature(
                        featureId=newFeatureId if newFeature else featureId,
                        setId=shapeType or -1,
                        featureType=geometry.wkbType(),
                    )

                    # Lendo os vértices da parte
                    vertexList: list[Vertex] = []
                    verticesIterator = part.vertices()
                    for vertex in verticesIterator:
                        vertexList.append(
                            Vertex(
                                vertexId=vertexId,
                                x=vertex.x(),
                                y=vertex.y(),
                                last=not verticesIterator.hasNext(),
                            )
                        )
                        vertexId += 1

                    # Montando os segmentos.
                    segmentsList: list[Segment] = []
                    for i in range(len(vertexList) - 1):
                        vertexA = vertexList[i]
                        vertexB = vertexList[i + 1]

                        if vertexA.x + self.tolerance < vertexB.x:
                            segmentsList.append(
                                Segment(
                                    segmentId=len(segmentsList),
                                    featureId=feature.featureId,
                                    setId=shapeType,
                                    a=vertexA,
                                    b=vertexB,
                                )
                            )
                        elif vertexB.x + self.tolerance < vertexA.x:
                            segmentsList.append(
                                Segment(
                                    segmentId=len(segmentsList),
                                    featureId=feature.featureId,
                                    setId=shapeType,
                                    a=vertexB,
                                    b=vertexA,
                                )
                            )
                        else:  # Vertical
                            if vertexA.y + self.tolerance < vertexB.y:
                                segmentsList.append(  # NOSONAR
                                    Segment(
                                        segmentId=len(segmentsList),
                                        featureId=feature.featureId,
                                        setId=shapeType,
                                        a=vertexA,
                                        b=vertexB,
                                    )
                                )
                            else:
                                segmentsList.append(  # NOSONAR
                                    Segment(
                                        segmentId=len(segmentsList),
                                        featureId=feature.featureId,
                                        setId=shapeType,
                                        a=vertexB,
                                        b=vertexA,
                                    )
                                )

                    feature.vertexList = vertexList
                    feature.segmentsList = segmentsList

                    if not newFeature:  # Feição original.
                        if partsIterator.hasNext():
                            feature.hasObservation = True
                            obs.set_value(featureId, msg_1)

                        featureSet.featuresList.append(feature)
                    else:  # Adicionar novo registro no ShapeFile.
                        feature.hasObservation = True
                        obs.set_value(partId, msg_2 + str(featureId) + ".")

                        featureSet.newFeaturesList.append(feature)
                        featureSet.newFeaturesAttributes.append(
                            NewFeatureAttributes(
                                featureId=newFeatureId,
                                attributes=self.readAttributes(
                                    layer, qgsFeature.id()
                                ),
                            )
                        )
                        newFeatureId += 1

            else:
                vertexList = (
                    [
                        Vertex(x=point.x(), y=point.y())
                        for point in geometry.asPolyline()
                    ]
                    if not geometry.isNull()
                    else []
                )
                if len(vertexList) == 1:
                    feature = Feature(
                        featureId=qgsFeature.id(),
                        setId=shapeType or -1,
                        featureType=geometry.wkbType(),
                        vertexList=vertexList,
                    )
                    feature.segmentsList = [
                        Segment(  # Montando um segmento degenerado!
                            segmentId=0,
                            featureId=feature.featureId,
                            setId=shapeType,
                            a=vertexList[0],
                            b=vertexList[0],
                        )
                    ]
                    if shapeType == 0:  # É bacia. Não processar o elemento!
                        feature.process = False
                        feature.hasObservation = True
                        obs.set_value(qgsFeature.id(), msg_3)
                else:  # Não tem vertices! Situação de erro do ShapeFile.
                    feature = Feature(
                        featureId=qgsFeature.id(),
                        setId=shapeType or -1,
                        featureType=geometry.wkbType(),
                        vertexList=vertexList,
                    )
                    feature.process = False
                    feature.hasObservation = True
                    obs.set_value(qgsFeature.id(), msg_3)
                featureSet.featuresList.append(feature)

        # Cadastrando demais atributos da figura.
        featureSet.obs = obs

        return featureSet

    # Function to read attributes from a QgsVectorLayer feature
    def readAttributes(
        self, layer: QgsVectorLayer, feature_id: int
    ) -> list[Attribute]:
        feature = next(layer.getFeatures(QgsFeatureRequest(feature_id)))
        attributes = []

        for field in layer.fields():
            field_name = field.name()
            field_type = field.type()
            value = feature[field_name]

            # Convert to string
            if field_type == QVariant.String:
                value = str(value)
            elif field_type == QVariant.Int:
                value = str(int(value))
            elif field_type == QVariant.Double:
                value = str(float(value))
            elif field_type == QVariant.Bool:
                value = str(bool(value))
            elif field_type == QVariant.Date:
                value = value.toString("yyyy-MM-dd")

            attributes.append(
                Attribute(
                    attr_name=field_name, attr_type=field_type, attr_value=value
                )
            )

        return attributes

    def createFeatureSet(
        self,
        newFileName: str,
        originalLayer: QgsVectorLayer,
        fields: QgsFields,
        log: Message,
    ) -> Optional[QgsVectorFileWriter]:
        options = QgsVectorFileWriter.SaveVectorOptions()
        options.actionOnExistingFile = (
            QgsVectorFileWriter.ActionOnExistingFile.CreateOrOverwriteFile
        )
        options.driverName = "ESRI Shapefile"
        options.fileEncoding = "UTF-8"

        # Create an empty SHP file with the specified geometry type
        writer = QgsVectorFileWriter.create(
            newFileName,
            fields,
            originalLayer.wkbType(),
            originalLayer.sourceCrs(),
            originalLayer.transformContext(),
            options,
        )

        if not writer or writer.hasError() != QgsVectorFileWriter.NoError:
            log.append(f"Error when creating SHP file: {writer.errorMessage()}")
            return None
        return writer

    def getFields(
        self, originalLayer: QgsVectorLayer, params: Params, hasObservation: bool
    ) -> QgsFields:
        fields = QgsFields(originalLayer.fields())

        if params.strahlerOrderType > 0:
            fields.append(QgsField("Strahler", QVariant.Int))

        if params.shreveOrderEnabled:
            fields.append(QgsField("Shreve", QVariant.Int))

        fields.append(QgsField("Sharp", QVariant.Double))

        if hasObservation:
            obs_field_name = "Obs:"
            fields.append(QgsField(obs_field_name, QVariant.String, len=80))

        fields.append(QgsField("Fluxo", QVariant.Int))
        return fields

    def copyFeature(
        self,
        feature: Feature,
        qgsFeature: QgsFeature,
        writer: QgsVectorFileWriter,
        fields: QgsFields,
        params: Params,
        attributes: Optional[list[Attribute]],
    ) -> None:
        # Create a new feature
        copy = QgsFeature(fields, feature.featureId)

        # Set the geometry of the feature
        copy.setGeometry(qgsFeature.geometry())

        # Set the attributes
        if attributes and len(attributes) > 0:
            for i, attr in enumerate(attributes):
                copy.setAttribute(i, attr.attr_value)
        else:
            for i, attribute in enumerate(qgsFeature.attributes()):
                copy.setAttribute(i, attribute)

        # Set the fluxo attribute
        copy.setAttribute("Fluxo", feature.flow)

        # Set additional attributes like Strahler and Shreve
        if params.strahlerOrderType > 0:
            copy.setAttribute("Strahler", feature.strahler)

        if params.shreveOrderEnabled:
            copy.setAttribute("Shreve", feature.shreve)

        if params.monitorPointEnabled:
            copy.setAttribute("Sharp", feature.sharp)

        writer.addFeature(copy)

    def saveFeatureSet(
        self, featureSet: FeatureSet, params: Params, log: Message
    ) -> None:
        fields = self.getFields(featureSet.raw, params, len(featureSet.obs.list) > 0)

        writer = self.createFeatureSet(
            params.newFileName, featureSet.raw, fields, log
        )
        if not writer:
            return

        # Gravando os registros já existentes no shapefile original.
        for feature in featureSet.featuresList:
            self.copyFeature(
                feature,
                featureSet.raw.getFeature(feature.featureId),
                writer,
                fields,
                params,
                None,
            )

        # Gravando os novos registros criados.
        for feature in featureSet.newFeaturesList:
            self.copyFeature(
                feature,
                featureSet.raw.getFeature(feature.featureId),
                writer,
                fields,
                params,
                featureSet.getNewFeatureAttributes(feature.featureId),
            )

        del writer

        # Copiando os arquivos de configuração.
        self.copyConfigFiles(params.drainageFileName, params.newFileName)

        QgsProject.instance().addMapLayer(
            QgsVectorLayer(params.newFileName, "Hydroflow Results", "ogr")
        )

    def copyConfigFiles(self, fileName: str, newFileName: str) -> None:
        original_path = Path(fileName).parent
        new_path = Path(newFileName).parent

        base = Path(fileName).stem
        new_base = Path(newFileName).stem

        # Copy any file with the same name and different extension
        for ext in [".cpg", ".prj", ".shx", ".qix", ".shp.xml"]:
            file = original_path / (base + ext)
            if file.exists():
                shutil.copy(file, new_path / (new_base + ext))
