from decimal import Decimal

from qgis.PyQt import QtWidgets


class Params:
    def __init__(
        self,
        origin: QtWidgets.QDialog,
        drainageFileName: str = "",
        boundaryFileName: str = "",
        toleranceXY: Decimal = Decimal(0),
        strahlerOrderType: int = 0,
        shreveOrderEnabled: bool = False,
        monitorPointEnabled: bool = False,
        monitorPointN: int = 5,
    ) -> None:
        self.origin = origin
        self.drainageFileName = drainageFileName
        self.boundaryFileName = boundaryFileName
        self.newFileName = ""
        self.toleranceXY = toleranceXY
        self.strahlerOrderType = strahlerOrderType
        self.shreveOrderEnabled = shreveOrderEnabled
        self.monitorPointEnabled = monitorPointEnabled
        self.monitorPointN = monitorPointN
