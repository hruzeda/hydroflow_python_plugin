from models.segment import Segment
from models.vertex import Vertex


class Feature:
    def __init__(
        self,
        id=-1,
        setId=-1,
        outletFeatureId=-1,
        feature_type=0,
        partCount=0,
        flow=0,
        strahler=0,
        shreve=0,
        vertex_list=None,
        segments_list=None,
        process=True,
        hasObservation=False,
    ):
        self.id = id
        self.setId = setId
        self.outletFeatureId = outletFeatureId
        self.feature_type = feature_type
        self.partCount = partCount
        self.flow = flow
        self.strahler = strahler
        self.shreve = shreve
        self.vertex_list: list[Vertex] = vertex_list or []
        self.segments_list: list[Segment] = segments_list or []
        self.process = process
        self.hasObservation = hasObservation

    def setClassification(self, flow: int, strahler: int, shreve: int):
        self.flow = flow
        self.strahler = strahler
        self.shreve = shreve

    def cleanup(self):
        self.vertex_list = []
        self.segments_list = []
