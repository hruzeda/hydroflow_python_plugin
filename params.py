from qgis.PyQt import QtWidgets


class Params:
    def __init__(
        self,
        origin: QtWidgets.QDialog,
        drainageFileName: str = "",
        boundaryFileName: str = "",
        toleranceXY: float = 0,
        strahlerOrderType: int = 0,
        shreveOrderEnabled: bool = False,
    ) -> None:
        self.origin = origin
        self.drainageFileName = drainageFileName
        self.boundaryFileName = boundaryFileName
        self.newFileName = ""
        self.toleranceXY = toleranceXY
        self.strahlerOrderType = strahlerOrderType
        self.shreveOrderEnabled = shreveOrderEnabled
