class FeatureSet:
    def __init__(self, featureId=0, fileName="", typeCode=0):
        self.featureSetId = featureId
        self.fileName = fileName
        self.typeCode = typeCode
        self.newFeaturesList = []
        self.quantidadeFeicoes = 0
        self.numNewFeatures = 0
        self.numAttributes = 0

    def setNewFeature(self, feicao):
        self.newFeaturesList.append(feicao)
        self.numNewFeatures += 1
