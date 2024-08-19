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
        vertexCount=0,
        vertex_list=None,
        segmentCount=0,
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
        self.vertexCount = vertexCount
        self.vertex_list = vertex_list or []
        self.segmentCount = segmentCount
        self.segments_list = segments_list or []
        self.process = process
        self.hasObservation = hasObservation
