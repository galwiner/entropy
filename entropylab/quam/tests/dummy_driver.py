class DummyInst(object):
    def __init__(self, name: str):
        self.name = name
        self.connection = None
        self._value = None

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, val: float):
        self._value = val

    def connect(self):
        self.connection = True
        print(f"opened connection to {self.name}")

    def close(self):
        self.connection = False
        print(f"closed connection to {self.name}")


class DummyDC(DummyInst):
    def __init__(self, name: str = ""):
        super().__init__(name)
        self._v1 = None
        self._start = None
        self._end = None
        self._step = None

    @property
    def v1(self):
        return self._v1

    @v1.setter
    def v1(self, val: float):
        self._v1 = val
        # print(f"instrument name {self.name}, set voltage to {val}")

    def sweep(self, start, end, step):
        self._start = start
        self._end = end
        self._step = step
