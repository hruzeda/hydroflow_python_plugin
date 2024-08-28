from PyQt5.QtCore import QDateTime

from ..params import Params


class Message:
    def __init__(self, params: Params) -> None:
        self.params = params
        self.time = QDateTime.currentDateTime()
        self.result = ""
        self.list: list[str] = []

    # def cleanup(self):
    #     self.list = []

    def append(self, message: str) -> None:
        self.list.append(message)

    def getHeader(self) -> str:
        temp_1 = ""
        comp = ""
        temp_2 = ""
        temp_3 = ""
        temp_res = ""
        classification = 0

        if self.params.strahlerOrderType == 1:
            temp_2 = "Ordens por Strahler"
            classification += 1
        elif self.params.strahlerOrderType == 2:
            temp_2 = "Ordens por Strahler relaxado"
            classification += 1

        if self.params.shreveOrderEnabled:
            classification += 2

        if classification == 0:
            comp = ""
            temp_3 = "Somente Fluxo."
        elif classification == 1:
            comp = "."
        elif classification == 2:
            comp = ""
            temp_3 = "Ordens por Shreve."
        elif classification == 3:
            comp = ";\n   "
            temp_3 = "Ordens por Shreve."

        temp_1 = "   " + temp_2 + comp + temp_3

        if self.result:
            temp_res = "\nResultado: " + self.result

        return (
            "HydroFlow 1.3\n=============\nProcessamento: "
            f"{self.time.toString('dd/MM/yyyy hh:mm:ss')}\n"
            f"Tolerância: {str(self.params.toleranceXY)}\n"
            f"Rede de drenagem: {self.params.drainageFileName}\n"
            f"Limite da área: {self.params.boundaryFileName + temp_res}\n"
            f"Inferir: \n{temp_1}\n"
            "---------------------------------------------------------------"
            "----------------------------------------------------"
        )

    def getFooter(self) -> str:
        return (
            "---------------------------------------------------------------"
            "----------------------------------------------------"
        )

    def hasMessage(self) -> bool:
        return len(self.list) > 0

    def retrieveMessage(self, index: int) -> str:
        if index < len(self.list):
            return self.list[index]
        return ""
