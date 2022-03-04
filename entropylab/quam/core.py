import os
import jsonpickle
from abc import ABC, abstractmethod
from munch import Munch
from typing import Any, Optional, Type, Callable, Union, Dict
import inspect
import dill as pickle
import copy

from entropylab.api.in_process_param_store import InProcessParamStore, ParamStore, MergeStrategy
from entropylab import LabResources, SqlAlchemyDB

from qualang_tools.config.parameters import ConfigVars, Parameter
from qualang_tools.config import ConfigBuilder
from qualang_tools.config.components import *
from qualang_tools.config.primitive_components import *
from qualang_tools.config.parameters import *

from qm.QuantumMachinesManager import QuantumMachinesManager


class QMInstrument(Munch):

    def __init__(self, host="127.0.0.1"):
        self._cb_types = (Element, ElementCollection, Waveform, Controller,
                          Mixer, IntegrationWeights, Pulse)
        self.config_builder_objects = Munch()
        self.config = dict()
        self.qm_manager = None
        self.host = host
        super().__init__()

    def add(self, obj):
        if isinstance(obj, self._cb_types):
            self.config_builder_objects[obj.name] = obj
        else:
            raise TypeError("Adding object of type %s is not supported".format(type(obj)))

    def build(self):
        cb = ConfigBuilder()
        for (_, v) in self.config_builder_objects.items():
            cb.add(v)
        self.config = cb.build()

    def upload_config(self):
        config = copy.deepcopy(self.config)
        self.build()
        if config != self.config:
            config = self.config
            self.qm_manager = QuantumMachinesManager(self.host).open_qm(config)

    def simulate(self, prog, simulation_config=None):
        self.upload_config()
        job = self.qm_manager.simulate(prog, simulation_config)
        job.result_handles.wait_for_all_values()
        return job

    def execute(self, prog, simulation_config=None):
        #self.qm_manager.close_all_quantum_machines()
        self.upload_config()
        job = self.qm_manager.execute(prog, simulation_config)
        job.result_handles.wait_for_all_values()
        return job


class ParamStoreConnector:
    @staticmethod
    def connect(path) -> InProcessParamStore:
        return InProcessParamStore(path)

class QuamBaseClass(ABC):

    def __init__(self, path):
        self.path = path
        self._paramStore = ParamStoreConnector.connect(os.path.join(path, "params.db"))
        self.config_vars = ConfigVars()
        self._instruments_store = LabResources(SqlAlchemyDB(path))
        self.instruments = Munch()

    def commit(self, label: str = None):
        return self.params.commit(label)

    def merge(self, theirs: Union[Dict, ParamStore],
              merge_strategy: Optional[MergeStrategy] = MergeStrategy.OURS):
        self.params.merge(theirs, merge_strategy)

    @property
    def params(self):
        return self._paramStore

    def load(self, c_id):
        self.params.checkout(c_id)
        #(self.config_vars, objs) = jsonpickle.decode(self._paramStore["config_objects"])
        (self.config_vars, objs) = pickle.loads(eval(self._paramStore["config_objects"]))
        for (k, v) in objs.items():
            self.instruments[k] = v
        self.set_config_vars()

    def save(self, objs=None):
        #self._paramStore["config_objects"] = jsonpickle.encode((self.config_vars, objs))
        self._paramStore["config_objects"] = repr(pickle.dumps((self.config_vars, objs)))
        # self._serialize_instruments()

    def _serialize_instruments(self):
        self._paramStore['instruments'] = {}
        for k, v in self.instruments.items():
            self._paramStore['instruments'][k] = {'name': k, 'methods': self._method_extract(v)}

    def _method_extract(self, obj):
        methods = inspect.getmembers(obj, predicate=inspect.ismethod)
        print("methods: ", methods)
        return {}

    def set_config_vars(self):
        self.config_vars.set(**without_keys(self.params, ["config_objects", "instruments"]))


# this class represents an entity that can control  instruments

class QuamElement(object):
    def __init__(self, **kwargs):
        self.instruments = Munch()
        super().__init__(**kwargs)

"""
class QuamQubitArray(object,list):
    def __init__(self, **kwargs):

        self._connectivity = {}
        super().__init__(**kwargs)

    def add_elements(self, element: QuamElement, connections: set = None):
        self.append(element)
        if connections is not None:
            self._connectivity[len(self._elements)] = connections

    def get_connectivity(self, qb_index=None):
        if qb_index is None:
            return self._connectivity
        else:
            return self._connectivity[qb_index]

    def show_connectivity(self):
        for k, v in self._connectivity.items():
            print(f"Qubit {k} connects to: {v}")
"""

def without_keys(d, keys):
    return {x: d[x] for x in d if x not in keys}
