from models.attribute import Attribute
from models.feature import Feature


class FeatureSet:
    def __init__(self, featureId=0, fileName="", typeCode=0):
        self.featureSetId = featureId
        self.fileName = fileName
        self.typeCode = typeCode
        self.featuresList: list[Feature] = []
        self.newFeaturesList: list[Feature] = []
        self.newFeaturesAttributes: list[Attribute] = []
        self.obs = None

    def getFeature(self, featureId):
        if featureId >= 0 and featureId < len(self.featuresList):
            return self.featuresList[featureId]
        elif featureId >= len(self.featuresList) and featureId < len(
            self.featuresList
        ) + len(self.newFeaturesList):
            return self.newFeaturesList[featureId - len(self.featuresList)]
        return None

    def setFeatureClassification(
        self, featureId: int, flow: int, strahler: int, shreve: int
    ):
        if featureId < len(self.featuresList):
            self.featuresList[featureId].setClassification(flow, strahler, shreve)
        else:
            self.newFeaturesList[featureId - len(self.featuresList)].setClassification(
                flow, strahler, shreve
            )

    def cleanup(self):
        # Limpando as feiçoes.
        for feature in self.featuresList:
            feature.cleanup()
        self.featuresList = []
        self.numFeatures = 0

        # Limpando as feiçoes novas.
        for feature in self.newFeaturesList:
            feature.cleanup()
        self.newFeaturesList = []
        self.numNewFeatures = 0

        # Limpando os atributos das feições novas.
        for attribute in self.newFeaturesAttributes:
            attribute.cleanup()
        self.newFeaturesAttributes = []

        # //Limpando as observações.
        if self.obs:
            self.obs.cleanup()
        self.obs = None

    def getNewFeatureAttributes(self, featureId: int) -> Attribute:
        attrs = None
        index = self.findAttributeIndex(0, self.quantidadeFeicoesNovas - 1, featureId)
        if index != -1:
            reg = self.atributosFeicoesNovas[index]
            attrs = reg.getAtributos()
        return attrs

    def findAttributeIndex(self, start: int, end: int, featureId: int) -> int:
        resposta = -1
        if start <= end:
            # Calculando o meio (indice).
            center = round((start + end) / 2)

            # Lendo o registro do meio.
            reg = self.newFeaturesAttributes[center]

            # Analisando.
            if featureId == reg.getIdFeicao():
                resposta = center
            elif featureId < reg.getIdFeicao():
                if center > start:
                    resposta = self.findAttributeIndex(start, center - 1, featureId)
            else:  # (idElemento > reg.getIdElemento)
                if center < end:
                    resposta = self.findAttributeIndex(center + 1, end, featureId)
        return resposta

    def getTotalFeatures(self):
        return len(self.featuresList) + len(self.newFeaturesList)
