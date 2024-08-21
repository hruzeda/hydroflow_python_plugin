from typing import Optional

from .attribute import Attribute


class NewFeatureAttribute:
    def __init__(self, attribute: Attribute, featureId: Optional[int] = -1):
        self.featureId = -1
        self.attribute = attribute
