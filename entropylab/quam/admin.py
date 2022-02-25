import numpy
from munch import Munch
from dataclasses import dataclass
from enum import Enum, auto
from typing import Any, Optional, Type, Callable
from attr import attr
from cached_property import cached_property
from tomlkit import value
import jsonpickle
import inspect

from qm.QuantumMachinesManager import QuantumMachinesManager
from qualang_tools.config import ConfigBuilder
from qualang_tools.config.components import *
from qualang_tools.config.primitive_components import *
from qualang_tools.config.parameters import *
from entropylab.quam.utils import DotDict
from entropylab.quam.core import QuamBaseClass, QuamElement, QMInstrument
from entropylab import LabResources, SqlAlchemyDB

class QuamAdmin(QuamBaseClass, Munch):

    def __init__(self, path: str = '.entropy'):
        super().__init__(path).__init__()

    def __repr__(self):
        return f"QuamAdmin({self.path})"

    def set_instrument(self, name: str, resource_class: Type, *args, **kwargs):
        if self._instruments_store.resource_exist(name):
            self._instruments_store.remove_resource(name)
            self._instruments_store.register_resource(name, resource_class, *args, **kwargs)
        else:
            self._instruments_store.register_resource(name, resource_class, *args, **kwargs)
        
        self.instruments[name] = self._instruments_store.get_resource(name)
        if resource_class == QMInstrument:
            self[name] = resource_class(*args, **kwargs)
        
    def remove_instrument(self, name: str):
        self._instruments_store.remove_resource(name)

    def remove_all_instruments(self):
        for res in self._instruments_store.all_resources():
            self._instruments_store.remove_resource(res)

    def build_qua_configurations(self):
        self.set_config_vars()
        for (k,v) in self.items():
            if isinstance(v, QMInstrument):
                v.build_qua_config()

    def commit(self, label:str):
        objs = []
        for (k,v) in self.items():
            if isinstance(v, QMInstrument):
                objs.append(v)
        super().save(objs)
        return super().commit(label)