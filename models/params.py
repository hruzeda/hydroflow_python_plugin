class Params:
    def __init__(
        self,
        basinFileName="",
        boundaryFileName="",
        toleranceXY=0,
        strahlerOrderType=0,
        shreveOrderEnabled=False,
        origin=0,
    ):
        self.basinFileName = basinFileName
        self.boundaryFileName = boundaryFileName
        self.toleranceXY = toleranceXY
        self.strahlerOrderType = strahlerOrderType
        self.shreveOrderEnabled = shreveOrderEnabled
        self.origin = origin
