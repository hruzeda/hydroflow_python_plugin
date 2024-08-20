class Geometry:
    def __init__(self, tolerance=0):
        self.tolerance = tolerance

    def smallerThan(self, a, b):
        return a + self.tolerance < b

    def equalsTo(self, a, b):
        return abs(a - b) <= self.tolerance
