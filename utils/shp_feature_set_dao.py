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
    QgsProject,
    QgsVectorFileWriter,
    QgsVectorLayer,
    QgsWkbTypes,
)

from ..models.attribute import Attribute
from ..models.feature import Feature
from ..models.feature_set import FeatureSet
from ..models.observation import Observation
from ..models.segment import Segment
from ..models.vertex import Vertex
from ..params import Params


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

        # Initialize variables
        features = []
        obs = Observation()
        feature_set = FeatureSet(shapeType, fileName, layer.wkbType(), obs)

        msg_1 = "Feição com partes multiplas. Veja: "
        # msg_2 = "Parte da feição FID"  # NOSONAR
        msg_3 = "Feição não processada."

        # Iterate over features (feicoes)
        for featureIndex, feature in enumerate(layer.getFeatures()):
            geometry = feature.geometry()
            if geometry.isMultipart():
                # Handle multipart geometries
                p = 0
                for part in geometry.parts():
                    vertex_list = []
                    iterator = part.vertices()
                    for point in iterator:
                        vertex_list.append(
                            Vertex(
                                vertexId=p,
                                x=point.x(),
                                y=point.y(),
                                last=iterator.hasNext(),
                            )
                        )
                        p += 1

                    segments_list: list[Segment] = []
                    for i in range(len(vertex_list) - 1):
                        vertexA = vertex_list[i]
                        vertexB = vertex_list[i + 1]

                        if vertexA.x + self.tolerancia < vertexB.x:
                            segments_list.append(
                                Segment(
                                    segmentId=len(segments_list),
                                    featureId=featureIndex,
                                    setId=shapeType,
                                    a=vertexA,
                                    b=vertexB,
                                )
                            )
                        elif vertexB.x + self.tolerancia < vertexA.x:
                            segments_list.append(
                                Segment(
                                    segmentId=len(segments_list),
                                    featureId=featureIndex,
                                    setId=shapeType,
                                    a=vertexB,
                                    b=vertexA,
                                )
                            )
                        else:  # Vertical
                            if vertexA.y + self.tolerancia < vertexB.y:
                                segments_list.append(  # NOSONAR
                                    Segment(
                                        segmentId=len(segments_list),
                                        featureId=featureIndex,
                                        setId=shapeType,
                                        a=vertexA,
                                        b=vertexB,
                                    )
                                )
                            else:
                                segments_list.append(  # NOSONAR
                                    Segment(
                                        segmentId=len(segments_list),
                                        featureId=featureIndex,
                                        setId=shapeType,
                                        a=vertexB,
                                        b=vertexA,
                                    )
                                )

                    # Create and store the Feicao object
                    feature_object = Feature(
                        featureId=feature.id(),
                        setId=shapeType,
                        featureType=geometry.wkbType(),
                        vertex_list=vertex_list,
                        segments_list=segments_list,
                    )
                    features.append(feature_object)

                    feature_object.hasObservation = True
                    obs.set_value(feature.id(), msg_1)
            else:
                # Handle singlepart geometries
                vertex_list = [
                    Vertex(x=point.x(), y=point.y())
                    for point in geometry.asPolyline()
                ]
                if len(vertex_list) == 1:
                    # Handle point geometries with a degenerate segment
                    feature_object = Feature(
                        featureId=feature.id(),
                        setId=shapeType,
                        featureType=geometry.wkbType(),
                        vertex_list=vertex_list,
                        segments_list=[
                            Segment(
                                segmentId=0,
                                featureId=featureIndex,
                                setId=shapeType,
                                a=vertex_list[0],
                                b=vertex_list[0],
                            )
                        ],
                    )
                    if shapeType == 0:
                        feature_object.process = False
                        feature_object.hasObservation = True
                        obs.set_value(feature.id(), msg_3)
                else:
                    # Handle normal geometries
                    feature_object = Feature(
                        featureId=feature.id(),
                        setId=shapeType,
                        featureType=geometry.wkbType(),
                        vertex_list=vertex_list,
                    )
                    feature_object.process = False
                    feature_object.hasObservation = True
                    obs.set_value(feature.id(), msg_3)
                features.append(feature_object)

        # Set the attributes for the figura (ConjuntoFeicao object)
        feature_set.featuresList = features
        feature_set.obs = obs

        return feature_set

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

    def createFeatureSet(self, fileName: str, geometryType: QgsWkbTypes):
        # Define the geometry type
        geometry_type_map = {
            QgsWkbTypes.PointGeometry: "Point",
            QgsWkbTypes.LineGeometry: "LineString",
            QgsWkbTypes.PolygonGeometry: "Polygon",
        }

        geometryType = geometry_type_map.get(geometryType, None)
        if not geometryType:
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
        origFeature: Feature,
        shpLayer: QgsVectorLayer,
        strahler: int,
        shreve: bool,
        attributes: Optional[list[Attribute]],
    ):
        # Create a new feature
        feature = QgsFeature(shpLayer.fields())

        # Set the geometry of the feature
        geometry = QgsGeometry.fromPolylineXY(
            [QgsPointXY(v.x, v.y) for v in origFeature.vertex_list]
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
        shpLayer.dataProvider().addFeature(feature)
        shpLayer.updateExtents()

    def saveFeatureSet(self, featureSet: FeatureSet, params: Params) -> None:
        self.createFeatureSet(params.newFileName, QgsWkbTypes.PolygonGeometry)
        shp_layer = QgsVectorLayer(params.newFileName, "Hydroflow Results", "ogr")

        # Write existing features
        for feature in featureSet.featuresList:
            self.saveRecord(
                feature,
                shp_layer,
                params.strahlerOrderType,
                params.shreveOrderEnabled,
                None,
            )

        # Write new features
        for feature in featureSet.newFeaturesList:
            attributes = featureSet.getNewFeatureAttributes(feature.featureId)
            self.saveRecord(
                feature,
                shp_layer,
                params.strahlerOrderType,
                params.shreveOrderEnabled,
                [attributes] if attributes else None,
            )

        shp_layer.updateExtents()
        self.copyConfigFiles(params.drainageFileName, params.newFileName)
        QgsProject.instance().addMapLayer(shp_layer)

    def copyConfigFiles(self, fileName: str, newFileName: str):
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
