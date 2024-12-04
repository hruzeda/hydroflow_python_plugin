from decimal import Decimal
from typing import Optional

from qgis.core import QgsGeometry

from .segment import Segment
from .vertex import Vertex


class Feature:
    def __init__(
        self,
        geometry: QgsGeometry,
        featureId: int = -1,
        setId: int = -1,
        mouthFeatureId: int = -1,
        featureType: int = 0,
        flow: int = 0,
        strahler: int = 0,
        shreve: int = 0,
        vertexList: Optional[list[Vertex]] = None,
        segmentsList: Optional[list[Segment]] = None,
        process: bool = True,
        hasObservation: bool = False,
    ) -> None:
        self.geometry = geometry
        self.featureId = featureId
        self.setId = setId
        self.mouthFeatureId = mouthFeatureId
        self.featureType = featureType
        self.flow = flow
        self.strahler = strahler
        self.shreve = shreve
        self.sharp: Optional[Decimal] = None
        self.vertexList = vertexList or []
        self.segmentsList = segmentsList or []
        self.process = process
        self.hasObservation = hasObservation

    def __str__(self) -> str:
        return (
            f"Feature {self.featureId + 1} ({self.featureType}), "
            f"Flow: {self.flow}, "
            f"Strahler: {self.strahler}, "
            f"Shreve: {self.shreve}, "
            f"Sharp: {self.sharp}, "
            f"Vertices: {len(self.vertexList)}, "
            f"Segments: {len(self.segmentsList)}"
        )
