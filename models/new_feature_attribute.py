from .attribute import Attribute


class NewFeatureAttribute:
    def __init__(self, attribute: Attribute, featureId: int = -1):
        self.featureId = featureId
        self.attribute = attribute
