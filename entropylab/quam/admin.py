import pickle
import numpy
from abc import ABC, abstractmethod
from munch import Munch
from dataclasses import dataclass
from enum import Enum, auto
from typing import Any, Optional
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
        #self._configBuilderComponents = []
        #self.params = Munch()
        self.instruments = Munch()
        super().__init__(**kwargs)


cb_objs = ["Controller", "Transmon", "ReadoutResonator"]
for obj in cb_objs:
    globals()["Quam" + obj] = type("Quam" + obj, (QuamElement, getattr(qua_components, obj)), {})


class QuamBaseClass(ABC):

    def __init__(self, path):
        self.path = path
        self._paramStore = ParamStoreConnector.connect(path)
        self.config_builder_objects = Munch()
        self._paramStore["quam_elements"]=Munch()
        self.elements = Munch()
        self.config_vars = ConfigVars()
    
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

        def without_keys(d, keys):
            return {x: d[x] for x in d if x not in keys}
        
        self.config_vars.set(**without_keys(self.params._params,
                                            ["config_vars", "quam_elements"]))
        for k in self.config_builder_objects.keys():
            cb.add(self.config_builder_objects[k])
        return cb.build()

    def load(self, c_id):
        self.params.checkout(c_id)
        if "quam_elements" in self.params.keys():
            for (k,v) in self.params["quam_elements"].items():
                self.config_builder_objects[k] = jsonpickle.decode(v)
                self.elements[k] = jsonpickle.decode(v)
        if "config_vars" in self.params.keys():
            self.config_vars = jsonpickle.decode(self.params["config_vars"])
            #print(self.config_vars.values.keys())

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
        for k in self.config_builder_objects.keys():
            str_obj = jsonpickle.encode(self.config_builder_objects[k])
            self._paramStore["quam_elements"][k] = str_obj
        self._paramStore["config_vars"] = jsonpickle.encode(self.config_vars)


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

    @property
    def element_names(self):
        return list(self.elements.keys())

    @property
    def QUA_element_names(self):
        return list(self.config_builder_objects.keys())

    def operations(self, elm_name:str):
        config = self.config
        if elm_name in config["elements"].keys():
            return list(config["elements"][elm_name]["operations"].keys())

    @property
    def user_params(self):
        return list(self.config_vars.values.keys())

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
       
    