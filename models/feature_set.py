from typing import Optional

from qgis.gui import Qgis

from ..models.observation import Observation
from .attribute import Attribute
from .feature import Feature
from .new_feature_attribute import NewFeatureAttribute


class FeatureSet:
    def __init__(
        self,
        featureSetId: Optional[int],
        fileName: str,
        typeCode: Qgis.WkbType,
        obs: Observation,
    ) -> None:
        self.featureSetId = featureSetId
        self.fileName = fileName
        self.typeCode = typeCode
        self.featuresList: list[Feature] = []
        self.newFeaturesList: list[Feature] = []
        self.newFeaturesAttributes: list[NewFeatureAttribute] = []
        self.obs = obs

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

    def cleanup(self) -> None:
        # Limpando as feiçoes.
        for feature in self.featuresList:
            feature.cleanup()
        self.featuresList = []

        # Limpando as feiçoes novas.
        for feature in self.newFeaturesList:
            feature.cleanup()
        self.newFeaturesList = []

        # Limpando os atributos das feições novas.
        self.newFeaturesAttributes = []

        # //Limpando as observações.
        if self.obs:
            self.obs.cleanup()

    def getNewFeatureAttributes(self, featureId: int) -> Optional[Attribute]:
        index = self.findAttributeIndex(0, len(self.newFeaturesList) - 1, featureId)
        if index != -1:
            reg = self.newFeaturesAttributes[index]
            return reg.attribute
        return None

    def findAttributeIndex(self, start: int, end: int, featureId: int) -> int:
        result = -1
        if start <= end:
            # Calculando o meio (indice).
            center = round((start + end) / 2)

            # Lendo o registro do meio.
            reg = self.newFeaturesAttributes[center]

            # Analisando.
            if featureId == reg.featureId:
                result = center
            elif featureId < reg.featureId:
                if center > start:
                    result = self.findAttributeIndex(start, center - 1, featureId)
            else:  # (idElemento > reg.getIdElemento)
                if center < end:
                    result = self.findAttributeIndex(center + 1, end, featureId)
        return result

    def getTotalFeatures(self) -> int:
        return len(self.featuresList) + len(self.newFeaturesList)
