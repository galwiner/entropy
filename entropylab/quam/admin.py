import pickle
import numpy
from abc import ABC, abstractmethod
from munch import Munch
from dataclasses import dataclass
from enum import Enum, auto
from typing import Any, Optional, Type, Callable
from attr import attr
from cached_property import cached_property
from tomlkit import value
import jsonpickle

from qm.QuantumMachinesManager import QuantumMachinesManager
from qualang_tools.config import ConfigBuilder
from qualang_tools.config import components as qua_components
from qualang_tools.config.components import *
from qualang_tools.config.primitive_components import *

from entropylab import LabResources, SqlAlchemyDB
from entropylab.api.param_store import InProcessParamStore, ParamStore, MergeStrategy
from qualang_tools.config.parameters import *
from entropylab.quam.utils import DotDict
from munch import Munch
import os


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
class QuamElement(object):
    def __init__(self, **kwargs):
        # self._configBuilderComponents = []
        # self.params = Munch()
        self.instruments = Munch()
        super().__init__(**kwargs)


cb_objs = ["Controller", "Transmon", "ReadoutResonator"]
for obj in cb_objs:
    globals()["Quam" + obj] = type("Quam" + obj, (QuamElement, getattr(qua_components, obj)), {})


def without_keys(d, keys):
    return {x: d[x] for x in d if x not in keys}


class InstVars(ConfigVars):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class QuamBaseClass(ABC):

    def __init__(self, path):
        self.path = path
        self._paramStore = ParamStoreConnector.connect(os.path.join(path, "params.db"))
        self.config_builder_objects = Munch()
        self._paramStore["config_objects"] = Munch()
        self.elements = Munch()
        self.config_vars = ConfigVars()
        self.inst_vars = InstVars()

    def commit(self, label: str = None):
        return self.params.commit(label)

    def merge(self, theirs: Union[Dict, ParamStore],
              merge_strategy: Optional[MergeStrategy] = MergeStrategy.OURS):
        self.params.merge(theirs, merge_strategy)

    @property
    def params(self):
        return self._paramStore

    def build_qua_config(self):
        cb = ConfigBuilder()
        self.config_vars.set(**without_keys(self.params._params,
                                            ["config_objects"]))
        for k in self.config_builder_objects.keys():
            cb.add(self.config_builder_objects[k])
        return cb.build()

    def load(self, c_id):
        self.params.checkout(c_id)
        (self.config_vars, self.config_builder_objects) = jsonpickle.decode(self.params["config_objects"])
        for k in self.config_builder_objects.keys():
            self.elements[k] = self.config_builder_objects[k]
        self.config_vars.set(**without_keys(self.params._params, ["config_objects"]))

    def save(self):
        self._paramStore["config_objects"] = jsonpickle.encode((self.config_vars,
                                                                self.config_builder_objects))


class QuamAdmin(QuamBaseClass):

    def __init__(self, path: str = '.entropy'):
        self._instruments_store = LabResources(SqlAlchemyDB(path))
        self.instruments = Munch()
        self._cb_types = (qua_components.Element, qua_components.ElementCollection,
                          qua_components.Waveform, qua_components.Controller, qua_components.Mixer,
                          qua_components.IntegrationWeights, qua_components.Pulse)

        super().__init__(path)

    def __repr__(self):
        return f"QuamAdmin({self.path})"

    def add(self, element):
        if isinstance(element, QuamElement):
            self.elements[element.name] = element
            if isinstance(element, self._cb_types):
                self.config_builder_objects[element.name] = element

    def set_instrument(self, name: str, resource_class: Type, *args, **kwargs):
        if self._instruments_store.resource_exist(name):
            self._instruments_store.remove_resource(name)
            self._instruments_store.register_resource(name, resource_class, *args, **kwargs)
        else:
            self._instruments_store.register_resource(name, resource_class, *args, **kwargs)

        self.instruments[name] = self._instruments_store.get_resource(name)

    def remove_instrument(self, name: str):
        self._instruments_store.remove_resource(name)

    def remove_all_instruments(self):
        for res in self._instruments_store.all_resources():
            self._instruments_store.remove_resource(res)

    def add_parameter(self, name: str, val: Any, persistent: bool = True):
        if persistent:
            self.params._params[name] = val
        self.config_vars.set(name=val)


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
        super().__init__(path)
        self._instrument_store = LabResources(SqlAlchemyDB(path))
        self.instrument_list = tuple(self._instrument_store.all_resources())

    def __repr__(self):
        return f"QuamOracle({self.path})"

    @property
    def element_names(self):
        return list(self.elements.keys())

    @property
    def QUA_element_names(self):
        return list(self.config_builder_objects.keys())

    def operations(self, elm_name: str):
        config = self.config
        if elm_name in config["elements"].keys():
            return list(config["elements"][elm_name]["operations"].keys())

    @property
    def user_params(self):
        return list(self.config_vars.params.keys())

    @property
    def integration_weights(self):
        return list(self.config["integration_weights"].keys())

    @cached_property
    def config(self):
        return self.build_qua_config()


class QuamUser(QuamBaseClass):

    def __init__(self, path='.entropy', host="127.0.0.1"):
        super().__init__(path)
        self.host = host
        self.elements = Munch()
        self.pulses = Munch()
        self.integration_weights = Munch()
        self._instrument_store = LabResources(SqlAlchemyDB(path))
        self.instrument_list = self._instrument_store.all_resources()

    def __repr__(self):
        return f"QuamUser({self.path})"

    @property
    def config(self):
        return self.build_qua_config()

    def execute_qua(self, prog, use_simulator=False, simulation_config=None):
        qmm = QuantumMachinesManager(host=self.host)
        qmm.close_all_quantum_machines()
        if use_simulator:
            job = qmm.simulate(self.config, prog, simulation_config)
        else:
            job = qmm.execute(self.config, prog, simulation_config)
        job.result_handles.wait_for_all_values()
        return job

    def load(self, c_id):
        super().load(c_id)
        config = self.config
        for elm in config["elements"].keys():
            self.elements[elm] = elm
        for elm in config["pulses"].keys():
            self.pulses[elm] = elm
        for elm in config["integration_weights"].keys():
            self.integration_weights[elm] = elm
