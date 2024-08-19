from PyQt5.QtCore import QDateTime


class Message:
    def __init__(self, params):
        self.params = params
        self.time = QDateTime.currentDateTime()
        self.result = ""
