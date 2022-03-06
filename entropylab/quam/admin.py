from typing import Type

from qualang_tools.config.components import *
from qualang_tools.config.primitive_components import *

from entropylab.quam.core import QuamBaseClass, QuamElement


class QuamAdmin(QuamBaseClass):
    def __init__(self, path: str = ".entropy"):
        self._cb_types = (
            Element,
            ElementCollection,
            Waveform,
            Controller,
            Mixer,
            IntegrationWeights,
            Pulse,
        )

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
            self._instruments_store.register_resource(
                name, resource_class, *args, **kwargs
            )
        else:
            self._instruments_store.register_resource(
                name, resource_class, *args, **kwargs
            )

        self.instruments[name] = self._instruments_store.get_resource(name)

    def remove_instrument(self, name: str):
        self._instruments_store.remove_resource(name)

    def remove_all_instruments(self):
        for res in self._instruments_store.all_resources():
            self._instruments_store.remove_resource(res)
