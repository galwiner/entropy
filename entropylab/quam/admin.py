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
from entropylab.api.param_store import InProcessParamStore
from qualang_tools.config.parameters import ConfigVars
from entropylab.quam.utils import DotDict


def quam_init(path='.'):
    # this function initializes the quam system (it will be part of the quam)

    quam = QuamUser(path)
    admin = QuamAdmin(path)
    oracle = QuamOracle(path)

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


class QuamBaseClass(ABC):

    def __init__(self, path):
        self.path = path
        self._paramStore = ParamStoreConnector.connect(path)
        self.config_builder_objects = DotDict()
        self.config_vars = ConfigVars()
        self.elements = DotDict()

    def commit(self, label: str = None):
        return self.params.commit(label)

    @property
    def params(self):
        return self._paramStore

    def build_qua_config(self):
        cb = ConfigBuilder()
        self.config_vars.set(**self.params._params)
        for k in self.config_builder_objects.keys():
            cb.add(self.config_builder_objects[k])
        return cb.build()

class QuamAdmin(QuamBaseClass):

    def __init__(self, path='.entropy'):
        # self.instruments = LabResources(SqlAlchemyDB(path))
        self._cb_types = (qua_components.Element, qua_components.ElementCollection,
                          qua_components.Waveform, qua_components.Controller, qua_components.Mixer,
                          qua_components.IntegrationWeights, qua_components.Pulse)

        super().__init__(path)

    def add(self, element):
        if isinstance(element, QuamElement):
            self.elements[element.name] = element
            if isinstance(element, self._cb_types):
                self.config_builder_objects[element.name] = element

    def add_parameter(self, name: str, val: Any, persistent: bool = True):
        if persistent:
            self.params._params[name] = val
        self.config_vars.set(name=val)

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

class QuamOracle(QuamBaseClass):

    def __init__(self, path='.entropy') -> None:

        self._config = {}
        super().__init__(path)

    @property
    def element_names(self):
        return list(self.elements.keys())

    @property
    def QUA_element_names(self):
        return list(self.config_builder_objects.keys())

    @property
    def operations(self, elm_name:str):
        pass

    @property
    def user_params(self):
        pass

    @property
    def integration_weights(self):
        pass


class QuamUser(QuamBaseClass):

    def __init__(self, path='.entropy'):
        super().__init__(path)