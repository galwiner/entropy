from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum, auto
from typing import Any
from attr import attr
from qualang_tools.config import ConfigBuilder
from qualang_tools.config.parameters import ConfigVar
from qualang_tools.config import components as qua_components
from tomlkit import value
from entropylab.quam.param_store import InProcessParamStore
from qualang_tools.config.parameters import ConfigVar
from entropylab.quam.utils import DotDict


class QCONTROLLERS(Enum):
    OPX = auto()
    OPXPlus = auto()
    OPY = auto()
    OPZ = auto()


# class Quam:

#     def __init__(self,path='.') -> None:
#         super().__init__()
#         self._resources = LabResources(db=path)


def quam_init(path='.', name=None):
    # this function initializes the quam system (it will be part of the quam)

    # quam = Quam(path,name)
    quam = None
    admin = QuamAdmin(path, name)
    # oracle = QuamOracle(path,name)
    oracle = None
    return admin, quam, oracle


# def create_quam(name,path,**kwargs):
#     #mk param store
#     #mk resources DB, or add to exisiting and save quam under the provided name
#     #check if name exists in current project, and if so return exception.
#     pass
class ParamStoreConnector:
    @staticmethod
    def connect(path) -> InProcessParamStore:
        return InProcessParamStore(path)


@dataclass
class UserParameter:
    key: str
    value

# p = UserParameter('this','that')


# ParamStore['this'] = 'that'


# this class represents an entity that can control  instruments
class QuamElement(ABC):
    def __init__(self, name: str) -> None:
        print('here')
        self.name = name
        self._configBuilderComponents = []
        # self.params = DotDict()
        self.instruments = DotDict()


def quam_component_facotry(qua_component_class,name):
    def constructor(self, **kwargs):
        print('ctor')
        nonlocal newcls
        super(newcls.__class__, self).__init__(**kwargs)

    newcls =type(name, (qua_component_class,QuamElement), {'__init__': constructor})
    return newcls

a=quam_component_facotry(qua_components.Transmon,'QuamTransmon')

cont  = qua_components.Controller(name='cont')

b=a(name='xmon', I=cont.analog_output(1), Q=cont.analog_output(2),
                            intermediate_frequency=50)



class QuamTransmon(qua_components.Transmon, QuamElement):
    def __init__(self, **kwargs):
        super(QuamTransmon, self).__init__(**kwargs)
a=QuamTransmon(name='xmon', I=cont.analog_output(1), Q=cont.analog_output(2),
                            intermediate_frequency=50)

class QuamReadoutResonator(qua_components.ReadoutResonator, QuamElement):
    def __init__(self, **kwargs):
        super(QuamReadoutResonator, self).__init__(**kwargs)


class QuamAdmin():

    def __init__(self, name: str = None, path='.entropy/paramStore.db') -> None:
        self._paramStore = ParamStoreConnector.connect(path)
        self.config_vars = ConfigVar()
        self.elements = DotDict()
        self.config_builder_objects = DotDict()
        self.name = name
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
