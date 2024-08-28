from .attribute import Attribute


class NewFeatureAttributes:
    def __init__(self, attributes: list[Attribute], featureId: int = -1):
        self.featureId = featureId
        self.attributes = attributes
