import shutil
from pathlib import Path
from typing import Any, Optional

from PyQt5.QtCore import QVariant
from qgis.core import (
    QgsFeature,
    QgsFeatureRequest,
    QgsField,
    QgsFields,
    QgsGeometry,
    QgsPointXY,
    QgsProject,
    QgsVectorFileWriter,
    QgsVectorLayer,
    QgsWkbTypes,
)

from ..models.attribute import Attribute
from ..models.feature import Feature
from ..models.feature_set import FeatureSet
from ..models.new_feature_attribute import NewFeatureAttributes
from ..models.observation import Observation
from ..models.segment import Segment
from ..models.vertex import Vertex
from ..params import Params


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
        for featureId, feature in enumerate(layer.getFeatures()):
            geometry = feature.geometry()
            if geometry.isMultipart():
                # Lendo as partes.
                vertexId = 0
                partsIterator = geometry.parts()
                for partId, part in enumerate(partsIterator):
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
                                    featureId=featureId,
                                    setId=shapeType,
                                    a=vertexA,
                                    b=vertexB,
                                )
                            )
                        elif vertexB.x + self.tolerance < vertexA.x:
                            segmentsList.append(
                                Segment(
                                    segmentId=len(segmentsList),
                                    featureId=featureId,
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
                                        featureId=featureId,
                                        setId=shapeType,
                                        a=vertexA,
                                        b=vertexB,
                                    )
                                )
                            else:
                                segmentsList.append(  # NOSONAR
                                    Segment(
                                        segmentId=len(segmentsList),
                                        featureId=featureId,
                                        setId=shapeType,
                                        a=vertexB,
                                        b=vertexA,
                                    )
                                )

                    if partId == 0:  # Feição original.
                        featureObject = Feature(
                            featureId=featureId,
                            setId=shapeType or -1,
                            featureType=geometry.wkbType(),
                            vertexList=vertexList,
                            segmentsList=segmentsList,
                        )
                        if partsIterator.hasNext():
                            featureObject.hasObservation = True
                            obs.set_value(featureId, msg_1)

                        featureSet.featuresList.append(featureObject)
                    else:  # Adicionar novo registro no ShapeFile.
                        featureObject = Feature(
                            featureId=newFeatureId,
                            setId=shapeType or -1,
                            featureType=geometry.wkbType(),
                            vertexList=vertexList,
                            segmentsList=segmentsList,
                        )
                        featureObject.hasObservation = True
                        obs.set_value(partId, msg_2 + str(featureId) + ".")

                        featureSet.newFeaturesList.append(featureObject)
                        featureSet.newFeaturesAttributes.append(
                            NewFeatureAttributes(
                                featureId=newFeatureId,
                                attributes=self.readAttributes(layer, feature.id()),
                            )
                        )
                        newFeatureId += 1

            else:
                vertexList = [
                    Vertex(x=point.x(), y=point.y())
                    for point in geometry.asPolyline()
                ]
                if len(vertexList) == 1:
                    featureObject = Feature(
                        featureId=feature.id(),
                        setId=shapeType or -1,
                        featureType=geometry.wkbType(),
                        vertexList=vertexList,
                        segmentsList=[
                            Segment(  # Montando um segmento degenerado!
                                segmentId=0,
                                featureId=featureId,
                                setId=shapeType,
                                a=vertexList[0],
                                b=vertexList[0],
                            )
                        ],
                    )
                    if shapeType == 0:  # É bacia. Não processar o elemento!
                        featureObject.process = False
                        featureObject.hasObservation = True
                        obs.set_value(feature.id(), msg_3)
                else:  # Não tem vertices! Situação de erro do ShapeFile.
                    featureObject = Feature(
                        featureId=feature.id(),
                        setId=shapeType or -1,
                        featureType=geometry.wkbType(),
                        vertexList=vertexList,
                    )
                    featureObject.process = False
                    featureObject.hasObservation = True
                    obs.set_value(feature.id(), msg_3)
                featureSet.featuresList.append(featureObject)

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

    def createFeatureSet(self, fileName: str, geometryType: QgsWkbTypes) -> bool:
        # Define the geometry type
        geometry_type_map = {
            QgsWkbTypes.PointGeometry: "Point",
            QgsWkbTypes.LineGeometry: "LineString",
            QgsWkbTypes.PolygonGeometry: "Polygon",
        }

        geometryType = geometry_type_map.get(geometryType, None)
        if not geometryType:
            return False

        # Create an empty SHP file with the specified geometry type
        writer = QgsVectorFileWriter(
            fileName, "UTF-8", QgsFields(), geometryType, None, "ESRI Shapefile"
        )

        if writer.hasError() != QgsVectorFileWriter.NoError:
            print(f"Error when creating SHP file: {writer.hasError()}")
            return False

        del writer  # Close the file and release resources
        return True

    def createNewTable(
        self,
        fileName: str,
        originalDbfTable: Any,
        params: Params,
        has_observation: bool,
    ) -> bool:
        # Create a new SHP file (which includes a DBF table)
        fields = QgsFields()

        # Add fields from the original DBF table
        for field in originalDbfTable.fields():
            fields.append(field)

        if params.strahlerOrderType > 0:
            fields.append(QgsField("Strahler", QVariant.Int))

        if params.shreveOrderEnabled:
            fields.append(QgsField("Shreve", QVariant.Int))

        # Adding custom fields based on conditions
        fluxo_field_name = "Fluxo"
        if has_observation:
            obs_field_name = "Obs:"
            fields.append(QgsField(obs_field_name, QVariant.String, len=80))

        # Add the new fields
        fields.append(QgsField(fluxo_field_name, QVariant.Int))

        # Create the SHP file with the new fields
        writer = QgsVectorFileWriter(
            fileName,
            "UTF-8",
            fields,
            QgsWkbTypes.PolygonGeometry,
            None,
            "ESRI Shapefile",
        )

        if writer.hasError() != QgsVectorFileWriter.NoError:
            print(f"Error creating SHP file with new fields: {writer.hasError()}")
            return False

        # Copy the records from the original table
        for feature in originalDbfTable.getFeatures():
            new_feature = QgsFeature(writer.fields())

            # Copy the geometry from the original feature
            new_feature.setGeometry(feature.geometry())

            # Copy the attribute values
            for i, field in enumerate(originalDbfTable.fields()):
                new_feature.setAttribute(i, feature[i])

            # Add the new feature to the writer
            writer.addFeature(new_feature)

        del writer  # Close the file and release resources
        return True

    def saveRecord(
        self,
        origFeature: Feature,
        origLayer: QgsVectorLayer,
        newLayer: QgsVectorLayer,
        strahler: int,
        shreve: bool,
        attributes: Optional[list[Attribute]],
    ) -> None:
        # Create a new feature
        feature = QgsFeature(origLayer.fields())

        # Set the geometry of the feature
        geometry = QgsGeometry.fromPolylineXY(
            [QgsPointXY(v.x, v.y) for v in origFeature.vertexList]
        )
        feature.setGeometry(geometry)

        # Set the attributes
        if attributes and len(attributes) > 0:
            for i, attr in enumerate(attributes):
                feature.setAttribute(i, attr.attr_value)

        # Set the fluxo attribute
        feature.setAttribute("Fluxo", origFeature.flow)

        # Set additional attributes like Strahler and Shreve
        if strahler > 0:
            feature.setAttribute("Strahler", origFeature.strahler)

        if shreve:
            feature.setAttribute("Shreve", origFeature.shreve)

        # Add the feature to the layer
        newLayer.dataProvider().addFeature(feature)
        newLayer.updateExtents()

    def saveFeatureSet(self, featureSet: FeatureSet, params: Params) -> None:
        self.createFeatureSet(params.newFileName, QgsWkbTypes.PolygonGeometry)
        shp_layer = QgsVectorLayer(params.newFileName, "Hydroflow Results", "ogr")

        # Gravando os registros já existentes no shapefile original.
        for feature in featureSet.featuresList:
            self.saveRecord(
                feature,
                featureSet.raw,
                shp_layer,
                params.strahlerOrderType,
                params.shreveOrderEnabled,
                None,
            )

        # Gravando os novos registros criados.
        for feature in featureSet.newFeaturesList:
            self.saveRecord(
                feature,
                featureSet.raw,
                shp_layer,
                params.strahlerOrderType,
                params.shreveOrderEnabled,
                featureSet.getNewFeatureAttributes(feature.featureId),
            )

        shp_layer.updateExtents()

        # Copiando os arquivos de configuração.
        self.copyConfigFiles(params.drainageFileName, params.newFileName)

        QgsProject.instance().addMapLayer(shp_layer)

    def copyConfigFiles(self, fileName: str, newFileName: str) -> None:
        original_path = Path(fileName).parent
        new_path = Path(newFileName).parent

        base = Path(fileName).stem
        new_base = Path(newFileName).stem

        # Copy .prj file
        prj_file = original_path / f"{base}.prj"
        new_prj_file = new_path / f"{new_base}.prj"
        if prj_file.exists():
            shutil.copyfile(prj_file, new_prj_file)

        # Copy .xml file
        xml_file = original_path / f"{Path(fileName).name}.xml"
        new_xml_file = new_path / f"{Path(newFileName).name}.xml"
        if xml_file.exists():
            shutil.copyfile(xml_file, new_xml_file)
