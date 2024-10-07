import shutil
from pathlib import Path
from typing import Optional

from PyQt5.QtCore import QVariant
from qgis.core import (
    QgsFeature,
    QgsFeatureRequest,
    QgsField,
    QgsFields,
    QgsLineSymbol,
    QgsPalLayerSettings,
    QgsProject,
    QgsProperty,
    QgsRuleBasedLabeling,
    QgsRuleBasedRenderer,
    QgsSymbolLayer,
    QgsTextBufferSettings,
    QgsTextFormat,
    QgsVectorFileWriter,
    QgsVectorLayer,
)
from qgis.PyQt.QtGui import QColor, QFont

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
    def load_feature_set(
        self, filename: str, basename: str, shape_type: int
    ) -> Optional[FeatureSet]:
        # Lendo o registro
        layer = QgsVectorLayer(filename, basename, "ogr")
        if not layer.isValid():
            print("Failed to load layer!")
            return None

        # Initialize variables
        obs = Observation()
        feature_set = FeatureSet(shape_type, filename, layer.wkbType(), obs, layer)

        msg_1 = "Feição com partes multiplas. Veja: "
        msg_2 = "Parte da feição FID "
        msg_3 = "Feição não processada."

        # Montando as feições
        new_feature_id = layer.featureCount()
        for feature_id, qgs_feature in enumerate(layer.getFeatures()):
            geometry = qgs_feature.geometry()
            if geometry.isMultipart():
                # Lendo as partes.
                vertex_id = 0
                parts_iterator = geometry.parts()
                for part_id, part in enumerate(parts_iterator):
                    new_feature = part_id > 0
                    feature = Feature(
                        featureId=new_feature_id if new_feature else feature_id,
                        setId=shape_type,
                        featureType=geometry.wkbType(),
                    )

                    # Lendo os vértices da parte
                    vertex_list: list[Vertex] = []
                    vertices_iterator = part.vertices()
                    for vertex in vertices_iterator:
                        vertex_list.append(
                            Vertex(
                                vertexId=vertex_id,
                                x=vertex.x(),
                                y=vertex.y(),
                                last=not vertices_iterator.hasNext(),
                            )
                        )
                        vertex_id += 1

                    # Montando os segmentos.
                    segments_list: list[Segment] = []
                    for i in range(len(vertex_list) - 1):
                        vertex_A = vertex_list[i]
                        vertex_B = vertex_list[i + 1]

                        # Determine the correct orientation
                        if vertex_A.x + self.tolerance < vertex_B.x or (
                            abs(vertex_A.x - vertex_B.x) < self.tolerance
                            and vertex_A.y + self.tolerance < vertex_B.y
                        ):
                            start, end = vertex_A, vertex_B
                        else:
                            start, end = vertex_B, vertex_A

                        # Create the segment once with determined start and end points
                        segments_list.append(
                            Segment(
                                segmentId=len(segments_list),
                                featureId=feature.featureId,
                                setId=shape_type,
                                a=start,
                                b=end,
                            )
                        )

                    feature.vertexList = vertex_list
                    feature.segmentsList = segments_list

                    if not new_feature:  # Feição original.
                        if parts_iterator.hasNext():
                            feature.hasObservation = True
                            obs.set_value(feature_id, msg_1)

                        feature_set.featuresList.append(feature)
                    else:  # Adicionar novo registro no ShapeFile.
                        feature.hasObservation = True
                        obs.set_value(part_id, msg_2 + str(feature_id) + ".")

                        feature_set.newFeaturesList.append(feature)
                        feature_set.newFeaturesAttributes.append(
                            NewFeatureAttributes(
                                featureId=new_feature_id,
                                attributes=self.read_attributes(
                                    layer, qgs_feature.id()
                                ),
                            )
                        )
                        new_feature_id += 1

            else:
                vertex_list = (
                    [
                        Vertex(x=point.x(), y=point.y())
                        for point in geometry.asPolyline()
                    ]
                    if not geometry.isNull()
                    else []
                )
                if len(vertex_list) == 1:
                    feature = Feature(
                        featureId=qgs_feature.id(),
                        setId=shape_type or -1,
                        featureType=geometry.wkbType(),
                        vertexList=vertex_list,
                    )
                    feature.segmentsList = [
                        Segment(  # Montando um segmento degenerado!
                            segmentId=0,
                            featureId=feature.featureId,
                            setId=shape_type,
                            a=vertex_list[0],
                            b=vertex_list[0],
                        )
                    ]
                    if shape_type == 0:  # É bacia. Não processar o elemento!
                        feature.process = False
                        feature.hasObservation = True
                        obs.set_value(qgs_feature.id(), msg_3)
                else:  # Não tem vertices! Situação de erro do ShapeFile.
                    feature = Feature(
                        featureId=qgs_feature.id(),
                        setId=shape_type or -1,
                        featureType=geometry.wkbType(),
                        vertexList=vertex_list,
                    )
                    feature.process = False
                    feature.hasObservation = True
                    obs.set_value(qgs_feature.id(), msg_3)
                feature_set.featuresList.append(feature)

        # Cadastrando demais atributos da figura.
        feature_set.obs = obs

        return feature_set

    # Function to read attributes from a QgsVectorLayer feature
    def read_attributes(
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

    def create_feature_set(
        self,
        new_filename: str,
        qgs_layer: QgsVectorLayer,
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
            new_filename,
            fields,
            qgs_layer.wkbType(),
            qgs_layer.sourceCrs(),
            qgs_layer.transformContext(),
            options,
        )

        if not writer or writer.hasError() != QgsVectorFileWriter.NoError:
            log.append(f"Error when creating SHP file: {writer.errorMessage()}")
            return None
        return writer

    def get_fields(
        self, qgs_layer: QgsVectorLayer, params: Params, has_observation: bool
    ) -> QgsFields:
        fields = QgsFields(qgs_layer.fields())

        if params.strahlerOrderType > 0:
            fields.append(QgsField("Strahler", QVariant.Int))

        if params.shreveOrderEnabled:
            fields.append(QgsField("Shreve", QVariant.Int))

        fields.append(QgsField("Sharp", QVariant.Double))

        if has_observation:
            obs_field_name = "Obs:"
            fields.append(QgsField(obs_field_name, QVariant.String, len=80))

        fields.append(QgsField("Fluxo", QVariant.Int))
        return fields

    def copy_feature(
        self,
        feature: Feature,
        qgs_feature: QgsFeature,
        writer: QgsVectorFileWriter,
        fields: QgsFields,
        params: Params,
        attributes: Optional[list[Attribute]],
    ) -> None:
        # Create a new feature
        copy = QgsFeature(fields, feature.featureId)

        # Set the geometry of the feature
        copy.setGeometry(qgs_feature.geometry())

        # Set the attributes
        if attributes and len(attributes) > 0:
            for i, attr in enumerate(attributes):
                copy.setAttribute(i, attr.attr_value)
        else:
            for i, attribute in enumerate(qgs_feature.attributes()):
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

    def save_feature_set(
        self, feature_set: FeatureSet, params: Params, log: Message
    ) -> None:
        fields = self.get_fields(
            feature_set.raw, params, len(feature_set.obs.list) > 0
        )

        writer = self.create_feature_set(
            params.newFileName, feature_set.raw, fields, log
        )
        if not writer:
            return

        # Gravando os registros já existentes no shapefile original.
        for feature in feature_set.featuresList:
            self.copy_feature(
                feature,
                feature_set.raw.getFeature(feature.featureId),
                writer,
                fields,
                params,
                None,
            )

        # Gravando os novos registros criados.
        for feature in feature_set.newFeaturesList:
            self.copy_feature(
                feature,
                feature_set.raw.getFeature(feature.featureId),
                writer,
                fields,
                params,
                feature_set.getNewFeatureAttributes(feature.featureId),
            )

        del writer

        # Copiando os arquivos de configuração.
        self._copy_config_files(params.drainageFileName, params.newFileName)

        new_layer = QgsVectorLayer(params.newFileName, "Hydroflow Results", "ogr")
        self._set_layer_style(new_layer)
        QgsProject.instance().addMapLayer(new_layer)
        self._set_label_rules(new_layer)
        new_layer.triggerRepaint()

    def _set_layer_style(self, layer: QgsVectorLayer) -> None:
        base_width = 0.25
        symbol = QgsLineSymbol.createSimple({"color": "blue"})
        symbol.symbolLayer(0).setDataDefinedProperty(
            QgsSymbolLayer.PropertyStrokeColor,
            QgsProperty.fromExpression("if(\"Sharp\" is NULL, 'blue', 'yellow')"),
        )
        symbol.symbolLayer(0).setDataDefinedProperty(
            QgsSymbolLayer.PropertyStrokeWidth,
            QgsProperty.fromExpression(f'{base_width} * "Strahler"'),
        )
        renderer = QgsRuleBasedRenderer(symbol)
        layer.setRenderer(renderer)

    def _set_label_rules(self, layer: QgsVectorLayer) -> None:
        buffer = QgsTextBufferSettings()
        buffer.setSize(1.0)
        buffer.setColor(QColor("white"))
        buffer.setEnabled(True)

        sharp_label = QgsPalLayerSettings()
        sharp_label.fieldName = "Sharp"
        sharp_label.priority = 100
        text_format = QgsTextFormat()
        text_format.setFont(QFont("Arial", 10))
        text_format.setColor(QColor("orange"))
        text_format.setBuffer(buffer)
        sharp_label.setFormat(text_format)
        sharp_label.placement = QgsPalLayerSettings.Line

        shreve_label = QgsPalLayerSettings()
        shreve_label.fieldName = "Shreve"
        shreve_label.priority = 35
        text_format = QgsTextFormat()
        text_format.setFont(QFont("Arial", 8))
        text_format.setColor(QColor("black"))
        text_format.setBuffer(buffer)
        shreve_label.setFormat(text_format)
        shreve_label.placement = QgsPalLayerSettings.Line

        root_rule = QgsRuleBasedLabeling.Rule(None)
        root_rule.appendChild(QgsRuleBasedLabeling.Rule(sharp_label))
        root_rule.appendChild(QgsRuleBasedLabeling.Rule(shreve_label))

        layer.setLabelsEnabled(False)
        layer.setLabeling(None)
        layer.setLabelsEnabled(True)
        layer.setLabeling(QgsRuleBasedLabeling(root_rule))

    def _copy_config_files(self, fileName: str, newFileName: str) -> None:
        original_path = Path(fileName).parent
        new_path = Path(newFileName).parent

        base = Path(fileName).stem
        new_base = Path(newFileName).stem

        # Copy any file with the same name and different extension
        for ext in [".cpg", ".prj", ".shx", ".qix", ".shp.xml"]:
            file = original_path / (base + ext)
            if file.exists():
                shutil.copy(file, new_path / (new_base + ext))
