import os
import jsonpickle
from abc import ABC, abstractmethod
from munch import Munch
from typing import Any, Optional, Type, Callable, Union, Dict

from entropylab.api.param_store import InProcessParamStore, ParamStore, MergeStrategy
from qualang_tools.config.parameters import ConfigVars, Parameter
from qualang_tools.config import components as qua_components
from qualang_tools.config import ConfigBuilder

class ParamStoreConnector:
    @staticmethod
    def connect(path) -> InProcessParamStore:
        return InProcessParamStore(path)

class QuamBaseClass(ABC):
    
    def __init__(self, path):
        self.path = path
        self._paramStore = ParamStoreConnector.connect(os.path.join(path, "params.db"))
        self.config_builder_objects = Munch()
        self._paramStore["config_objects"] = Munch()
        self.elements = Munch()
        self.config_vars = ConfigVars()

    def commit(self, label: str = None):
        self.save()
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
                                            ["config_objects", "instruments"]))
        for k in self.config_builder_objects.keys():
            cb.add(self.config_builder_objects[k])
        return cb.build()

    def load(self, c_id):
        self.params.checkout(c_id)
        (self.config_vars, self.config_builder_objects) = jsonpickle.decode(self.params["config_objects"])
        for k in self.config_builder_objects.keys():
            self.elements[k] = self.config_builder_objects[k]
        self.config_vars.set(**without_keys(self.params._params, ["config_objects", "instruments"]))

    def save(self):
        self._paramStore["config_objects"] = jsonpickle.encode((self.config_vars,
                                                                self.config_builder_objects))


# this class represents an entity that can control  instruments
class QuamElement(object):
    def __init__(self, **kwargs):
        self.instruments = Munch()
        super().__init__(**kwargs)

cb_objs = ["Controller", "Transmon", "ReadoutResonator"]
for obj in cb_objs:
    globals()["Quam" + obj] = type("Quam" + obj, (QuamElement, getattr(qua_components, obj)), {})

def without_keys(d, keys):
    return {x: d[x] for x in d if x not in keys}

class QuamFluxTunableXmon(qua_components.Transmon, QuamElement):
    def __init__(self, flux_channel, *args, **kwargs):
        self.flux_channel = flux_channel
        super().__init__(*args, **kwargs)