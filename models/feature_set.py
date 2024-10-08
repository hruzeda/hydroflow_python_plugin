from decimal import Decimal
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
        self,
        featureId: int,
        flow: Optional[int] = None,
        strahler: Optional[int] = None,
        shreve: Optional[int] = None,
        sharp: Optional[Decimal] = None,
    ) -> None:
        if featureId < len(self.featuresList):
            feature = self.featuresList[featureId]
        else:
            feature = self.newFeaturesList[featureId - len(self.featuresList)]

        if flow:
            feature.flow = flow

        if strahler:
            feature.strahler = strahler

        if shreve:
            feature.shreve = shreve

        if sharp:
            feature.sharp = sharp

    def getNewFeatureAttributes(self, featureId: int) -> Optional[list[Attribute]]:
        for reg in self.newFeaturesAttributes:
            if featureId == reg.featureId:
                return reg.attributes
        return None

    def getTotalFeatures(self) -> int:
        return len(self.featuresList) + len(self.newFeaturesList)
