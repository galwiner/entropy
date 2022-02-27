import os
import jsonpickle
from abc import ABC, abstractmethod
from munch import Munch
from typing import Any, Optional, Type, Callable, Union, Dict
import inspect

from entropylab.api.in_process_param_store import InProcessParamStore, ParamStore, MergeStrategy
from entropylab import LabResources, SqlAlchemyDB

from qualang_tools.config.parameters import ConfigVars, Parameter
from qualang_tools.config import ConfigBuilder
from qualang_tools.config.components import *
from qualang_tools.config.primitive_components import *
from qualang_tools.config.parameters import *


class QMInstrument(object):

    def __init__(self):
        self._cb_types = (Element, ElementCollection, Waveform, Controller,
                          Mixer, IntegrationWeights, Pulse)
        self.config_builder_objects = []
        self.config = dict()

    def add(self, obj):
        if isinstance(obj, self._cb_types):
            self.config_builder_objects.append(obj)
        else:
            raise TypeError("Adding object of type %s is not supported".format(type(obj)))

    def build_qua_config(self):
        cb = ConfigBuilder()
        for k in self.config_builder_objects:
            cb.add(k)
        self.config = cb.build()


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
        (self.config_vars, objs) = jsonpickle.decode(self._paramStore["config_objects"])
        for (k, v) in objs.items():
            self.instruments[k] = v
        self.set_config_vars()

    def save(self, objs=None):
        self._paramStore["config_objects"] = jsonpickle.encode((self.config_vars, objs))
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


def without_keys(d, keys):
    return {x: d[x] for x in d if x not in keys}
