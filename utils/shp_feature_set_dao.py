import os
import shutil
from decimal import Decimal
from pathlib import Path
from typing import Any, Optional

from PyQt5.QtCore import QMetaType
from qgis.core import (
    QgsFeature,
    QgsFeatureRequest,
    QgsField,
    QgsFields,
    QgsGeometry,
    QgsLineSymbol,
    QgsPalLayerSettings,
    QgsProject,
    QgsProperty,
    QgsRuleBasedLabeling,
    QgsRuleBasedRenderer,
    QgsSimpleFillSymbolLayer,
    QgsSymbolLayer,
    QgsTextBufferSettings,
    QgsTextFormat,
    QgsVectorFileWriter,
    QgsVectorLayer,
    QgsWkbTypes,
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
    def __init__(self, tolerance: Decimal = Decimal(0)) -> None:
        self.tolerance = tolerance
        self.error_msg = "Feição não processada."

    # Tipos: 0 - bacia; 1 - limite.
    def load_feature_set(
        self, filename: str, basename: str, shape_type: int
    ) -> Optional[FeatureSet]:
        # Lendo o registro
        layer = QgsVectorLayer(filename, basename, "ogr")
        if not layer.isValid():
            return None

        # Initialize variables
        obs = Observation()
        feature_set = FeatureSet(shape_type, filename, layer.wkbType(), obs, layer)

        # Montando as feições
        feature_id = 0
        for qgs_feature in layer.getFeatures(QgsFeatureRequest()):
            geometry = qgs_feature.geometry()
            if geometry.isMultipart():
                feature_id = self._parse_multi_part_feature(
                    feature_id,
                    feature_set,
                    qgs_feature,
                    geometry,
                    layer,
                    shape_type,
                    obs,
                )

            else:
                self._parse_single_part_feature(
                    feature_id, feature_set, geometry, shape_type, obs
                )
                feature_id += 1

        # Cadastrando demais atributos da figura.
        feature_set.obs = obs

        return feature_set

    def _parse_multi_part_feature(
        self,
        feature_id: int,
        feature_set: FeatureSet,
        qgs_feature: QgsFeature,
        geometry: QgsGeometry,
        layer: QgsVectorLayer,
        shape_type: int,
        obs: Observation,
    ) -> int:
        # Lendo as partes.
        parts = self._get_raw_parts(geometry)
        for part_id, rings_or_lines in enumerate(parts):
            feature = Feature(
                geometry=QgsGeometry.fromMultiPolylineXY(rings_or_lines)
                if isinstance(rings_or_lines[0], list)
                else QgsGeometry.fromPolylineXY(rings_or_lines),
                featureId=feature_id + part_id,
                setId=shape_type,
                featureType=geometry.wkbType(),
            )

            # Lendo os vértices da parte
            vertex_list: list[Vertex] = self._parse_vertices(rings_or_lines)

            # Montando os segmentos.
            segments_list = self._parse_segments(shape_type, feature, vertex_list)

            feature.vertexList = vertex_list
            feature.segmentsList = segments_list

            if part_id == 0:  # Feição original.
                if part_id < len(parts) - 1:
                    feature.hasObservation = True
                    obs.set_value(feature_id, "Feição com partes multiplas. Veja: ")

                feature_set.featuresList.append(feature)
            else:  # Adicionar novo registro no ShapeFile.
                feature.hasObservation = True
                obs.set_value(part_id, f"Parte da feição FID {feature_id + 1}.")

                feature_set.newFeaturesList.append(feature)
                feature_set.newFeaturesAttributes.append(
                    NewFeatureAttributes(
                        featureId=feature_id + part_id,
                        attributes=self.read_attributes(layer, qgs_feature.id()),
                    )
                )

        return feature_id + len(parts)

    def _get_raw_parts(self, geometry: QgsGeometry) -> list[Any]:
        if (
            geometry.wkbType() == QgsWkbTypes.MultiLineString
            or QgsWkbTypes.flatType(geometry.wkbType()) == QgsWkbTypes.LineGeometry
        ):
            return list(geometry.asMultiPolyline())
        if geometry.wkbType() == QgsWkbTypes.MultiPolygon:
            return list(geometry.asMultiPolygon())
        return list(geometry.asPolyline())

    def _parse_vertices(self, rings_or_lines: list[Any]) -> list[Vertex]:
        vertex_list = []
        vertex_id = 0
        for i, ring_or_line in enumerate(rings_or_lines):
            if not isinstance(ring_or_line, list):
                ring_or_line = [ring_or_line]

            for j, point in enumerate(ring_or_line):
                vertex_list.append(
                    Vertex(
                        vertexId=vertex_id,
                        x=Decimal(point.x()),
                        y=Decimal(point.y()),
                        last=i == len(rings_or_lines) - 1
                        and j == len(ring_or_line) - 1,
                    )
                )
                vertex_id += 1
        return vertex_list

    def _parse_segments(
        self, shape_type: int, feature: Feature, vertex_list: list[Vertex]
    ) -> list[Segment]:
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

            segments_list.append(
                Segment(
                    segmentId=len(segments_list),
                    featureId=feature.featureId,
                    setId=shape_type,
                    a=start,
                    b=end,
                )
            )

        return segments_list

    def _parse_single_part_feature(
        self,
        feature_id: int,
        feature_set: FeatureSet,
        geometry: QgsGeometry,
        shape_type: int,
        obs: Observation,
    ) -> None:
        vertex_list = (
            [Vertex(x=point.x(), y=point.y()) for point in geometry.asPolyline()]
            if not geometry.isNull()
            else []
        )
        if len(vertex_list) == 1:
            feature = Feature(
                geometry,
                featureId=feature_id,
                setId=shape_type,
                featureType=geometry.wkbType(),
                vertexList=vertex_list,
            )

            feature.segmentsList = [
                Segment(  # Montando um segmento degenerado!
                    segmentId=0,
                    featureId=0,
                    setId=shape_type,
                    a=vertex_list[0],
                    b=vertex_list[0],
                )
            ]

            if shape_type == 0:  # É bacia. Não processar o elemento!
                feature.process = False
                feature.hasObservation = True
                obs.set_value(0, self.error_msg)

        else:  # Não tem vertices! Situação de erro do ShapeFile.
            feature = Feature(
                geometry,
                featureId=feature_id,
                setId=shape_type,
                featureType=geometry.wkbType(),
                vertexList=vertex_list,
            )
            feature.process = False
            feature.hasObservation = True

            obs.set_value(0, self.error_msg)

        feature_set.featuresList.append(feature)

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
            if field_type == QMetaType.Type.QString:
                value = str(value)
            elif field_type == QMetaType.Type.Int:
                value = str(int(value))
            elif field_type == QMetaType.Type.Double:
                value = str(Decimal(value))
            elif field_type == QMetaType.Type.Bool:
                value = str(bool(value))
            elif field_type == QMetaType.Type.QDate:
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

        fields.append(QgsField("FID", QMetaType.Type.Int))
        fields.append(QgsField("Fluxo", QMetaType.Type.Int))

        if params.strahlerOrderType > 0:
            fields.append(QgsField("Strahler", QMetaType.Type.Int))

        if params.shreveOrderEnabled:
            fields.append(QgsField("Shreve", QMetaType.Type.Int))

        fields.append(QgsField("Sharp", QMetaType.Type.Double))

        if has_observation:
            obs_field_name = "Obs:"
            fields.append(QgsField(obs_field_name, QMetaType.Type.QString, len=80))

        return fields

    def copy_feature(
        self,
        featureId: int,
        feature: Feature,
        qgs_feature: QgsFeature,
        writer: QgsVectorFileWriter,
        fields: QgsFields,
        params: Params,
        attributes: Optional[list[Attribute]],
    ) -> None:
        # Create a new feature
        copy = QgsFeature(fields, featureId)

        # Set the geometry of the feature
        copy.setGeometry(self._check_geometry_flow(feature))

        # Set the attributes
        if attributes and len(attributes) > 0:
            for i, attr in enumerate(attributes):
                copy.setAttribute(i, attr.attr_value)
        else:
            for i, attribute in enumerate(qgs_feature.attributes()):
                copy.setAttribute(i, attribute)

        copy.setAttribute("FID", featureId + 1)

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

    def _check_geometry_flow(self, feature: Feature) -> QgsGeometry:
        if feature.flow == 2:
            rings_or_lines = self._get_raw_parts(feature.geometry)
            inverted = rings_or_lines[::-1]
            if isinstance(inverted[0], list):
                inverted_parts = []
                for part in enumerate(inverted):
                    inverted_parts.append(part[::-1])
                return QgsGeometry.fromMultiPolylineXY(inverted_parts)
            return QgsGeometry.fromPolylineXY(inverted)
        return feature.geometry

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
        featureCount = 0
        for feature in feature_set.featuresList:
            self.copy_feature(
                featureCount,
                feature,
                feature_set.raw.getFeature(feature.featureId),
                writer,
                fields,
                params,
                None,
            )
            featureCount += 1

        # Gravando os novos registros criados.
        for new_feature in feature_set.newFeaturesList:
            self.copy_feature(
                featureCount,
                new_feature,
                feature_set.raw.getFeature(new_feature.featureId),
                writer,
                fields,
                params,
                feature_set.getNewFeatureAttributes(new_feature.featureId),
            )
            featureCount += 1

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

        # Set up fill and border
        symbol = QgsLineSymbol.createSimple({"color": "blue"})

        fill_layer = QgsSimpleFillSymbolLayer()
        fill_layer.setColor(QColor("blue"))
        fill_layer.setDataDefinedProperty(
            QgsSymbolLayer.PropertyStrokeColor,
            QgsProperty.fromExpression("if(\"Sharp\" is NULL, 'blue', 'yellow')"),
        )
        fill_layer.setDataDefinedProperty(
            QgsSymbolLayer.PropertyStrokeWidth,
            QgsProperty.fromExpression(f'{base_width} * "Strahler"'),
        )

        border_layer = QgsSimpleFillSymbolLayer()
        border_layer.setColor(QColor("black"))
        border_layer.setStrokeWidth(1)

        symbol.appendSymbolLayer(fill_layer)
        symbol.appendSymbolLayer(border_layer)

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
        for ext in [".cpg", ".prj", ".shx", ".qix", ".shp.xml", ".shp.gpkg"]:
            new_file_path = new_path / (new_base + ext)
            if Path(new_file_path).exists():
                os.remove(new_file_path)

            file = original_path / (base + ext)
            if file.exists():
                shutil.copy(file, new_path / (new_base + ext))
