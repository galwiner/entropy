class DummyInst:
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
        self.connection = 'open'
        print(self.connection)

    def close(self):
        self.connection = 'closed'
        print(self.connection)
