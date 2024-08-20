import shutil
from pathlib import Path
from typing import Optional

from PyQt5.QtCore import QVariant
from qgis.core import (
    QgsFeature,
    QgsFeatureRequest,
    QgsField,
    QgsFields,
    QgsGeometry,
    QgsPointXY,
    QgsVectorFileWriter,
    QgsVectorLayer,
    QgsWkbTypes,
)

from models.attribute import Attribute
from models.feature import Feature
from models.feature_set import FeatureSet
from models.observation import Observation
from models.params import Params
from models.vertex import Vertex


class SHPFeatureSetDAO:
    def __init__(self, tolerancia=0):
        self.tolerancia = tolerancia

    # Function to read and process SHP files using QgsVectorLayer
    def loadFeatureSet(
        self, fileName: str, baseName: str, shapeType: Optional[int] = None
    ) -> Optional[FeatureSet]:
        # Load the SHP file as a vector layer
        layer = QgsVectorLayer(fileName, baseName, "ogr")
        if not layer.isValid():
            print("Failed to load layer!")
            return None

        feature_set = FeatureSet(shapeType, fileName, layer.wkbType())

        # Initialize variables
        features = []
        obs = Observation()
        msg_1 = "Feição com partes multiplas. Veja: "
        # msg_2 = "Parte da feição FID"  # NOSONAR
        msg_3 = "Feição não processada."

        # Iterate over features (feicoes)
        for feature in layer.getFeatures():
            geometry = feature.geometry()
            if geometry.isMultipart():
                # Handle multipart geometries
                parts = (
                    geometry.asMultiPolygon()
                    if geometry.type() == QgsWkbTypes.PolygonGeometry
                    else geometry.asMultiLineString()
                )
                for part in parts:
                    vertex_list = []
                    for point in part:
                        vertex_list.append(Vertex(x=point.x(), y=point.y()))

                    # Create and store the Feicao object
                    feature_object = Feature(
                        id=feature.id(),
                        setId=shapeType,
                        feature_type=geometry.wkbType(),
                        vertex_list=vertex_list,
                    )
                    features.append(feature_object)

                    if len(parts) > 1:
                        feature_object.setTemObservacao(True)
                        obs.setObservacao(feature.id(), msg_1)
            else:
                # Handle singlepart geometries
                vertex_list = [
                    Vertex(x=point.x(), y=point.y()) for point in geometry.asPolyline()
                ]
                if len(vertex_list) == 1:
                    # Handle point geometries with a degenerate segment
                    feature_object = Feature(
                        id=feature.id(),
                        setId=shapeType,
                        feature_type=geometry.wkbType(),
                        vertex_list=vertex_list,
                    )
                    feature_object.setProcessar(False)
                    feature_object.setTemObservacao(True)
                    obs.setObservacao(feature.id(), msg_3)
                else:
                    # Handle normal geometries
                    feature_object = Feature(
                        id=feature.id(),
                        setId=shapeType,
                        feature_type=geometry.wkbType(),
                        vertex_list=vertex_list,
                    )
                features.append(feature_object)

        # Set the attributes for the figura (ConjuntoFeicao object)
        feature_set.featuresList = features
        feature_set.obs = obs

        return feature_set

    # Function to read attributes from a QgsVectorLayer feature
    def readAttributes(self, layer, feature_id):
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
                Attribute(attr_name=field_name, attr_type=field_type, attr_value=value)
            )

        return attributes

    def createFeatureSet(self, fileName, geometryType):
        # Define the geometry type
        geometry_type_map = {
            QgsWkbTypes.PointGeometry: "Point",
            QgsWkbTypes.LineGeometry: "LineString",
            QgsWkbTypes.PolygonGeometry: "Polygon",
        }

        geometryType = geometry_type_map.get(geometryType, None)
        if geometryType is None:
            return None

        # Create an empty SHP file with the specified geometry type
        writer = QgsVectorFileWriter(
            fileName, "UTF-8", QgsFields(), geometryType, None, "ESRI Shapefile"
        )

        if writer.hasError() != QgsVectorFileWriter.NoError:
            print(f"Error when creating SHP file: {writer.hasError()}")
            return None

        del writer  # Close the file and release resources
        return True

    def createNewTable(self, fileName, originalDbfTable, params, has_observation):
        # Create a new SHP file (which includes a DBF table)
        fields = QgsFields()

        # Add fields from the original DBF table
        for field in originalDbfTable.fields():
            fields.append(field)

        if params.tipoOrdemStrahler > 0:
            fields.append(QgsField("Strahler", QVariant.Int))

        if params.eOrdemShreve:
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
        origFeature,
        shpLayer,
        strahler,
        shreve,
        attributes,
        numAttributes,
    ):
        # Create a new feature
        feature = QgsFeature(shpLayer.fields())

        # Set the geometry of the feature
        geometry = QgsGeometry.fromPolylineXY(
            [QgsPointXY(v.getX(), v.getY()) for v in origFeature.getVertices()]
        )
        feature.setGeometry(geometry)

        # Set the attributes
        if attributes and numAttributes > 0:
            for i, atributo in enumerate(attributes):
                feature.setAttribute(i, atributo.getValor())

        # Set the fluxo attribute
        feature.setAttribute("Fluxo", origFeature.getFluxo())

        # Set additional attributes like Strahler and Shreve
        if strahler > 0:
            feature.setAttribute("Strahler", origFeature.getStrahler())

        if shreve:
            feature.setAttribute("Shreve", origFeature.getShreve())

        # Add the feature to the layer
        shpLayer.dataProvider().addFeature(feature)
        shpLayer.updateExtents()

    def saveFeatureSet(self, featureSet: FeatureSet, params: Params) -> None:
        shp_layer = QgsVectorLayer(params.getNomeNovoArquivo(), "New Layer", "ogr")
        if not shp_layer.isValid():
            print("Error opening new SHP layer")
            return

        # Write existing features
        for i in range(featureSet.getQuantidadeFeicoes()):
            feature = featureSet.getFeicao(i)
            self.saveRecord(
                feature,
                shp_layer,
                params.getTipoOrdemStrahler(),
                params.getEOrdemShreve(),
                None,
                0,
            )

        # Write new features
        for j in range(featureSet.getQuantidadeFeicoesNovas()):
            feature = featureSet.getFeicaoNova(j)
            attributes = featureSet.getNewFeatureAttributes(feature.getId())
            self.saveRecord(
                feature,
                shp_layer,
                params.getTipoOrdemStrahler(),
                params.getEOrdemShreve(),
                attributes,
                featureSet.getQuantidadeAtributos(),
            )

        shp_layer.updateExtents()

    def copyConfigFiles(self, fileName, newFileName):
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
