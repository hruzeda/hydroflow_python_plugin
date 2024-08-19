class IteratorItem:
    def __init__(self, point=None, event_type=-1, segmentA=None, segmentB=None):
        self.point = point
        self.eventType = event_type
        self.segmentA = segmentA
        self.segmentB = segmentB


class Iterator:
    def __init__(self, geo):
        self.geo = geo
        self.lines = []
        self.points = []

    def next(self):
        if len(self.lines) == 0:
            return self.lines.pop()
