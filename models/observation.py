class ObservationItem:
    def __init__(self):
        self.featureId = 0
        self.text = ""


class Observation:
    def __init__(self):
        self.list = []

    def get_value(self, featureId):
        for item in self.list:
            if item.featureId == featureId:
                return item.texto
        return ""

    def set_value(self, featureId, text):
        found = False
        if len(self.list) > 0:
            for pos in range(len(self.list)):
                item = self.list[pos]
                if item.featureId == featureId:
                    item.text = text
                    found = True
                    break

        if not found:
            item = ObservationItem()
            item.featureId = featureId
            item.text = text
            self.list.append(item)
