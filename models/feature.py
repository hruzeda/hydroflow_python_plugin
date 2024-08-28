from .segment import Segment
from .vertex import Vertex


class Feature:
    def __init__(
        self,
        featureId=-1,
        setId=-1,
        mouthFeatureId=-1,
        featureType=0,
        flow=0,
        strahler=0,
        shreve=0,
        vertexList=None,
        segmentsList=None,
        process=True,
        hasObservation=False,
    ) -> None:
        self.featureId = featureId
        self.setId = setId
        self.mouthFeatureId = mouthFeatureId
        self.featureType = featureType
        self.flow = flow
        self.strahler = strahler
        self.shreve = shreve
        self.vertexList: list[Vertex] = vertexList or []
        self.segmentsList: list[Segment] = segmentsList or []
        self.process = process
        self.hasObservation = hasObservation

    def setClassification(self, flow: int, strahler: int, shreve: int) -> None:
        self.flow = flow
        self.strahler = strahler
        self.shreve = shreve

    def cleanup(self) -> None:
        self.vertexList = []
        self.segmentsList = []

    def __str__(self) -> str:
        return (
            f"Feature {self.featureId} ({self.featureType}), "
            f"Flow: {self.flow}, "
            f"Strahler: {self.strahler}, "
            f"Shreve: {self.shreve}, "
            f"Vertices: {len(self.vertexList)}, "
            f"Segments: {len(self.segmentsList)}"
        )
