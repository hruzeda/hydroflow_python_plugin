from typing import Optional

from qgis.gui import Qgis

from .attribute import Attribute
from .feature import Feature
from .new_feature_attribute import NewFeatureAttribute
from .observation import Observation


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
        index = self.findAttributeIndex(featureId)
        if index != -1:
            reg = self.newFeaturesAttributes[index]
            return reg.attribute
        return None

    def findAttributeIndex(self, featureId: int) -> int:
        i = round(len(self.newFeaturesAttributes) / 2)
        while 0 <= i < len(self.newFeaturesAttributes):
            # Calculando o meio (indice).

            # Lendo o registro do meio.
            reg = self.newFeaturesAttributes[i]

            # Analisando.
            if featureId == reg.featureId:
                return i
            if featureId < reg.featureId:
                i -= 1
            else:
                i += 1
        return -1

    def getTotalFeatures(self) -> int:
        return len(self.featuresList) + len(self.newFeaturesList)
