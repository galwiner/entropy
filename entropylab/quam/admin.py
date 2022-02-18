import numpy
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
from qualang_tools.config.components import *
from qualang_tools.config.primitive_components import *
from qualang_tools.config.parameters import *
from entropylab.quam.utils import DotDict
from entropylab.quam.core import QuamBaseClass, QuamElement
from entropylab import LabResources, SqlAlchemyDB

class QuamAdmin(QuamBaseClass):

    def __init__(self, path: str = '.entropy'):
        self._instruments_store = LabResources(SqlAlchemyDB(path))
        self.instruments = Munch()
        self._cb_types = (Element, ElementCollection, Waveform, Controller, Mixer,
                          IntegrationWeights, Pulse)

        super().__init__(path)

    def __repr__(self):
        return f"QuamAdmin({self.path})"

    def save(self):
        super().save()
        self._paramStore['instruments'] = self._serialize_instruments()

    def _serialize_instruments(self):
        self._paramStore['instruments'] = {}
        for k, v in self.instruments.items():
            self._paramStore['instruments'][k] = {'name': k, 'methods': self._method_extract(v)}
    def _method_extract(self,obj):
        return {}
    
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