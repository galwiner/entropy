from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum, auto
from typing import Any
from attr import attr
from qualang_tools.config import ConfigBuilder
from qualang_tools.config.parameters import ConfigVar
from qualang_tools.config import components as qua_components
from tomlkit import value

from entropylab import LabResources, SqlAlchemyDB
from entropylab.quam.param_store import InProcessParamStore
from qualang_tools.config.parameters import ConfigVar
from entropylab.quam.utils import DotDict


def quam_init(path='.', name=None):
    # this function initializes the quam system (it will be part of the quam)

    # quam = Quam(path,name)
    quam = None
    admin = QuamAdmin(path, name)
    # oracle = QuamOracle(path,name)
    oracle = None
    return admin, quam, oracle


class ParamStoreConnector:
    @staticmethod
    def connect(path) -> InProcessParamStore:
        return InProcessParamStore(path)


# this class represents an entity that can control  instruments
class QuamElement:
    def __init__(self, name: str) -> None:
        print('here')
        self.name = name
        self._configBuilderComponents = []
        # self.params = DotDict()
        self.instruments = DotDict()


def quam_component_facotry(qua_component_class, name):
    def constructor(self, **kwargs):
        nonlocal newcls
        super(QuamElement, self).__init__()
        super(newcls, self).__init__(**kwargs)

    newcls = type(name, (qua_component_class, QuamElement), {'__init__': constructor})
    return newcls


a = quam_component_facotry(qua_components.Transmon, 'QuamTransmon')

cont = qua_components.Controller(name='cont')

b = a(name='xmon', I=cont.analog_output(1), Q=cont.analog_output(2),
      intermediate_frequency=50)


)


class MyClass:
    def __init__(self):
        self.collection1 = DotDict()
        self.collection2 = DotDict()

    def _find(self,name:str):
        if name in self.collection1.keys():
            self.collection1[name]
        elif name in self.collection2.keys():
            self.collection2[name]


    def __getattribute__(self, name: str) -> Any:
        print(name)
        return super().__getattribute__(name)
        if hasattr(value, 'keys'):
            value = DotDict(value)
        if name in self.collection1.keys():
            self.collection1[name]
        elif name in self.collection2.keys():
            self.collection2[name]

my= MyClass()
my.collection1.a=1
my.collection2.b=2
print(my.a)
print(my.b)

class QuamTransmon(QuamElement, qua_components.Transmon):
    def __init__(self, **kwargs):
        super(QuamTransmon, self).__init__(**kwargs)
        super(QuamElement, self).__init__()


kwargs = {'name': 'xmon', 'I': cont.analog_output(1), 'Q': cont.analog_output(2),
          'intermediate_frequency': 50}

a = QuamTransmon(**kwargs)


class QuamReadoutResonator(qua_components.ReadoutResonator, QuamElement):
    def __init__(self, **kwargs):
        super(QuamReadoutResonator, self).__init__(**kwargs)


class QuamAdmin():

    def __init__(self, name: str = None, path='.entropy') -> None:
        self._paramStore = ParamStoreConnector.connect(path)
        self.config_vars = ConfigVar()
        self.elements = DotDict()
        self.config_builder_objects = DotDict()
        self.name = name
        self.instruments = LabResources(SqlAlchemyDB(path))
        self._cb_types = (qua_components.Element, qua_components.ElementCollection,
                          qua_components.Waveform, qua_components.Controller, qua_components.Mixer,
                          qua_components.IntegrationWeights, qua_components.Pulse)

    def add(self, element):
        if isinstance(element, QuamElement):
            self.elements[element.name] = element
            if isinstance(element, self._cb_types):
                self.config_builder_objects[element.name] = element

    def add_parameter(self, name: str, val: Any, persistent: bool = True):
        if persistent:
            self._paramStore._params[name] = val
        self._configVar.set(name=val)

    def commit(self, label: str = None):
        self._paramStore.commit(label)

    @property
    def params(self):
        return self._paramStore

    def build_qua_config(self):
        cb = ConfigBuilder()
        self.config_vars.set(**self._paramStore._params)
        for k in self.config_builder_objects.keys():
            cb.add(self.config_builder_objects[k])
        return cb.build()

        #inside add_instrument use labResources
    def add_instrument(self,name,instrument):
        self.instruments.register_resource(name,instrument)

    admin.add_instrument(name="flux_driver", DummyInst)

        def mySetter(val):
            def volt_from_MHZ(val):
                return ((val + 3) /12)
            admin.flux_driver.v = volt_from_MHZ(val)

        xmon.add_attribute('flux',admin.flux_driver.v_from_MHz)

        admin.add(xmon)
        admin.save_to_store()

        quam.xmon.flux = 1