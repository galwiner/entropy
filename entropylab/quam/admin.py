import pickle
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum, auto
from typing import Any
from attr import attr
from qualang_tools.config import ConfigBuilder

from qualang_tools.config import components as qua_components
from tomlkit import value
from entropylab import LabResources, SqlAlchemyDB
from entropylab.quam.param_store import InProcessParamStore
from qualang_tools.config.parameters import ConfigVars
from entropylab.quam.utils import DotDict


def quam_init(path='.', name=None):
    # this function initializes the quam system (it will be part of the quam)

    # quam = Quam(path,name)
    quam = None
    admin = QuamAdmin(path, name)
    oracle = QuamOracle(path, name)
    # oracle = None
    return admin, quam, oracle


class ParamStoreConnector:
    @staticmethod
    def connect(path) -> InProcessParamStore:
        return InProcessParamStore(path)


# this class represents an entity that can control  instruments
class QuamElement(ABC):
    def __init__(self, **kwargs):
        self._configBuilderComponents = []
        # self.params = DotDict()
        self.instruments = DotDict()
        super().__init__(**kwargs)


cb_objs = ["Controller", "Transmon", "ReadoutResonator"]
for obj in cb_objs:
    globals()["Quam" + obj] = type("Quam" + obj, (QuamElement, getattr(qua_components, obj)), {})


class QuamAdmin():

    def __init__(self, name: str = None, path='.entropy') -> None:
        self.path = path
        self._paramStore = ParamStoreConnector.connect(path)
        self.config_vars = ConfigVars()
        self.elements = DotDict()
        self.config_builder_objects = DotDict()
        self.name = name
        # self.instruments = LabResources(SqlAlchemyDB(path))
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
        self.config_vars.set(name=val)

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

    def save(self):
        with open(self.path + '/pickle.pkl', 'wb') as f:
            pickle.dump(self, f)


#     def add_instrument(self, name, class_name, args, kwargs):
#         self.instruments.register_resource(name, class_name, args, kwargs)
#         setattr(self,name,WrapperForDriver(class_name,name))
#
# class WrapperForDriver:
#
#     def __init__(self,class_name,instrument_name) -> None:
#         super().__init__()
#
#     def __getattribute__(self, name: str) -> Any:
#         return FunctionInfo(class_name,instrument_name,name)
# #FunctionInfo -> dictionary with instrument name, function names, parameter names

class QuamOracle():

    def __init__(self, name: str = None, path='.entropy/paramStore.db') -> None:
        self._paramStore = ParamStoreConnector.connect(path)
        self.elements = DotDict()
        self.config_builder_objects = DotDict()
        self.config_vars = None
        self._config = {}

    @property
    def get_elements(self):
        return list(self.elements.keys())

    @property
    def get_QUA_elements(self):
        return list(self.config_builder_objects.keys())

    def build_qua_config(self):
        cb = ConfigBuilder()
        self.config_vars.set(**self._paramStore._params)
        print(self.config_vars.values)
        print(self._paramStore._params)
        for k in self.config_builder_objects.keys():
            cb.add(self.config_builder_objects[k])
        self._config = cb.build()
