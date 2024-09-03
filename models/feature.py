from typing import Optional

from .segment import Segment
from .vertex import Vertex


class Feature:
    def __init__(
        self,
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
        self.featureId = featureId
        self.setId = setId
        self.mouthFeatureId = mouthFeatureId
        self.featureType = featureType
        self.flow = flow
        self.strahler = strahler
        self.shreve = shreve
        self.vertexList = vertexList or []
        self.segmentsList = segmentsList or []
        self.process = process
        self.hasObservation = hasObservation

    def setClassification(self, flow: int, strahler: int, shreve: int) -> None:
        self.flow = flow
        self.strahler = strahler
        self.shreve = shreve

    # def cleanup(self) -> None:
    #     self.vertexList = []
    #     self.segmentsList = []

    def __str__(self) -> str:
        return (
            f"Feature {self.featureId} ({self.featureType}), "
            f"Flow: {self.flow}, "
            f"Strahler: {self.strahler}, "
            f"Shreve: {self.shreve}, "
            f"Vertices: {len(self.vertexList)}, "
            f"Segments: {len(self.segmentsList)}"
        )
