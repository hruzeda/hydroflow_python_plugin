from qgis.PyQt import QtWidgets


class Params:
    def __init__(
        self,
        origin: QtWidgets.QDialog,
        basinFileName="",
        boundaryFileName="",
        toleranceXY=0,
        strahlerOrderType=0,
        shreveOrderEnabled=False,
    ):
        self.origin = origin
        self.basinFileName = basinFileName
        self.boundaryFileName = boundaryFileName
        self.newFileName = ""
        self.toleranceXY = toleranceXY
        self.strahlerOrderType = strahlerOrderType
        self.shreveOrderEnabled = shreveOrderEnabled
