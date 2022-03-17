from typing import Type, Optional, Any

from munch import Munch
from qualang_tools.config.components import Controller

from entropylab.quam._element_access import _AdminElementAccess
from entropylab.quam.core import _QuamCore, DatabaseWrapper
from entropylab.quam.instruments_wrappers import InstrumentAccess
from entropylab.quam.quam_components import _QuamParameters


class ParametersValueWrapper(Munch):
    is_frozen = False

    def __init__(self, parameters: _QuamParameters) -> None:
        super().__init__()
        self._parameters: _QuamParameters = parameters
        self.is_frozen = True

    # def __getitem__(self, item):
    #     if self.is_frozen:
    #         params = super().__getitem__("_parameters")
    #         return params[item]
    #     else:
    #         super(ParametersWrapper, self).__getitem__(item)
    #
    def __getattr__(self, key):
        if self.is_frozen:
            params: _QuamParameters = super().__getattr__("_parameters")
            return params.parameter(key).value  # TODO is it doing what it should?
        else:
            super(ParametersValueWrapper, self).__getattr__(key)

    def __setattr__(self, key, value):
        if self.is_frozen:
            params: _QuamParameters = super().__getattr__("_parameters")
            params.parameter(key).set_value(value)
        else:
            super(ParametersValueWrapper, self).__setattr__(key, value)

    def __setitem__(self, key, value):
        if self.is_frozen:
            params: _QuamParameters = super().__getattr__("_parameters")
            params.parameter(key).set_value(value)
        else:
            super(ParametersValueWrapper, self).__setitem__(key, value)

    def list_names(self):
        params: _QuamParameters = super().__getattr__("_parameters")
        return set(params.get_names())


class QuamAdmin:
    def __init__(self, path):
        super().__init__()
        if isinstance(path, _QuamCore):
            self._core = path
        else:
            self._core = _QuamCore(path)
        self._instruments = InstrumentAccess(self._core.instruments)
        self._params_wrapper = ParametersValueWrapper(self._core.parameters)

    def __repr__(self):
        return f"QuamAdmin({self._core.path})"

    def add(self, element):  # TODO good type hint
        self._core.add(element)

    def add_instrument(self, name: str, resource_class: Type, *args, **kwargs):
        self._core.set_instrument(name, resource_class, *args, **kwargs)

    def update_instrument(self, name: str, resource_class: Type, *args, **kwargs):
        self._core.set_instrument(name, resource_class, *args, **kwargs)

    def remove_instrument(self, name: str):
        self._core.remove_resource(name)

    def parameter(self, name, setter=None, **kwargs) -> Any:
        kwargs.get("initial")  # for type hint
        return self._core.new_parameter(name, setter, **kwargs)

    @property
    def elements(self) -> _AdminElementAccess:
        return _AdminElementAccess(self._core.elements._elements_dicts, None)

    @property
    def user_parameters(self) -> ParametersValueWrapper:
        return self._params_wrapper

    @property
    def database(self) -> DatabaseWrapper:
        return DatabaseWrapper(self._core.database)

    @property
    def instruments(self) -> InstrumentAccess:
        return self._instruments

    def commit(self, label):
        return self._core.commit(label)

    def checkout(
        self,
        commit_id: Optional[str] = None,
        commit_num: Optional[int] = None,
        move_by: Optional[int] = None,
    ):
        return self._core.checkout(
            commit_id=commit_id, commit_num=commit_num, move_by=move_by
        )

    def set_qop(self, arg=None, host=None, port=None):
        self._core.set_qop(arg, host, port)

    def add_controller(self, name, type):
        # TODO maybe query qop
        # TODO should it return QuamElement?
        cont = Controller(name)
        self._core.add(cont)
        return cont

    def set_default_commit(self, commit_id):
        self._core.set_default_commit(commit_id)

    @property
    def commit_id(self):
        return self._core.get_current_commit()
