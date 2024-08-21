class Vertex:
    def __init__(self, id=-1, x=0, y=0, last=False):
        self.id = id
        self.x = x
        self.y = y
        self.last = last

    def equalsTo(self, p: "Vertex"):
        return self.x == p.x and self.y == p.y

    def withinIteratorRow(self, x: float, tolerance: float):
        return abs(x - self.x) <= tolerance

    def isExtremity(self):
        return self.id == 0 or self.last
