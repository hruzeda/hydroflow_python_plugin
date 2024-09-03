from typing import Optional

from qgis.core import QgsVectorLayer
from qgis.gui import Qgis

from .attribute import Attribute
from .feature import Feature
from .new_feature_attribute import NewFeatureAttributes
from .observation import Observation


class FeatureSet:
    def __init__(
        self,
        featureSetId: Optional[int],
        fileName: str,
        typeCode: Qgis.WkbType,
        obs: Observation,
        raw: QgsVectorLayer,
    ) -> None:
        self.featureSetId = featureSetId
        self.fileName = fileName
        self.typeCode = typeCode
        self.featuresList: list[Feature] = []
        self.newFeaturesList: list[Feature] = []
        self.newFeaturesAttributes: list[NewFeatureAttributes] = []
        self.obs = obs
        self.raw = raw

    def getFeature(self, featureId: int) -> Optional[Feature]:
        if 0 <= featureId < len(self.featuresList):
            return self.featuresList[featureId]
        if len(self.featuresList) <= featureId < self.getTotalFeatures():
            return self.newFeaturesList[featureId - len(self.featuresList)]
        return None

    def setFeatureClassification(
        self, featureId: int, flow: int, strahler: int, shreve: int
    ) -> None:
        if featureId < len(self.featuresList):
            self.featuresList[featureId].setClassification(flow, strahler, shreve)
        else:
            self.newFeaturesList[
                featureId - len(self.featuresList)
            ].setClassification(flow, strahler, shreve)

    # def cleanup(self) -> None:
    #     # Limpando as feiçoes.
    #     for feature in self.featuresList:
    #         feature.cleanup()
    #     self.featuresList = []

    #     # Limpando as feiçoes novas.
    #     for feature in self.newFeaturesList:
    #         feature.cleanup()
    #     self.newFeaturesList = []

    #     # Limpando os atributos das feições novas.
    #     self.newFeaturesAttributes = []

    #     # //Limpando as observações.
    #     if self.obs:
    #         self.obs.cleanup()

    def getNewFeatureAttributes(self, featureId: int) -> Optional[list[Attribute]]:
        for reg in self.newFeaturesAttributes:
            if featureId == reg.featureId:
                return reg.attributes
        return None

    def getTotalFeatures(self) -> int:
        return len(self.featuresList) + len(self.newFeaturesList)
