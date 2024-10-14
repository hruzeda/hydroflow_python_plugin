class ObservationItem:
    def __init__(self) -> None:
        self.featureId = 0
        self.text = ""


class Observation:
    def __init__(self) -> None:
        self.list: list[ObservationItem] = []

    def get_value(self, featureId: int) -> str:
        for item in self.list:
            if item.featureId == featureId:
                return item.text
        return ""

    def set_value(self, featureId: int, text: str) -> None:
        found = False
        for item in self.list:
            if item.featureId == featureId:
                item.text = text
                found = True
                break

        if not found:
            item = ObservationItem()
            item.featureId = featureId
            item.text = text
            self.list.append(item)
