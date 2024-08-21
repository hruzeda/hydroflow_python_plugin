from .segment import Segment
from .vertex import Vertex


class Feature:
    def __init__(
        self,
        featureId=-1,
        setId=-1,
        mouthFeatureId=-1,
        featureType=0,
        partCount=0,
        flow=0,
        strahler=0,
        shreve=0,
        vertex_list=None,
        segments_list=None,
        process=True,
        hasObservation=False,
    ) -> None:
        self.featureId = featureId
        self.setId = setId
        self.mouthFeatureId = mouthFeatureId
        self.featureType = featureType
        self.partCount = partCount
        self.flow = flow
        self.strahler = strahler
        self.shreve = shreve
        self.vertex_list: list[Vertex] = vertex_list or []
        self.segments_list: list[Segment] = segments_list or []
        self.process = process
        self.hasObservation = hasObservation

    def setClassification(self, flow: int, strahler: int, shreve: int) -> None:
        self.flow = flow
        self.strahler = strahler
        self.shreve = shreve

    def cleanup(self) -> None:
        self.vertex_list = []
        self.segments_list = []
