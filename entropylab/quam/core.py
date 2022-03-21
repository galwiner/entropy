import dataclasses
import os
from json import JSONEncoder
from types import MethodType
from typing import Optional, Union, Dict, List

from munch import Munch
from qm.QuantumMachinesManager import QuantumMachinesManager
from qualang_tools.config import ConfigBuilder
from qualang_tools.config.primitive_components import ConfigBuilderElement

from entropylab import LabResources, SqlAlchemyDB
from entropylab.api.in_process_param_store import (
    InProcessParamStore,
    ParamStore,
    MergeStrategy,
)
from entropylab.quam.instruments_wrappers import FunctionRef, FunctionInfo
from entropylab.quam.quam_components import (
    _dict_to_config_builder,
    _QuamParameters,
    _QuamElements,
    _config_builder_to_dict,
)

DEFAULT_COMMIT = "default.commit"

_PARAMETERS = "_parameters_"
_ELEMENTS = "elements"
_QOP_INFO = "_qop_info_"


class CustomJSONEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, FunctionRef):
            dic = obj.__dict__
            dic["type_cls"] = "FunctionInfo"
            return dic
        return JSONEncoder.default(self, obj)


class ParamStoreConnector:
    @staticmethod
    def connect(path) -> InProcessParamStore:
        return InProcessParamStore(path, custom_encoder=CustomJSONEncoder)


@dataclasses.dataclass
class QopInfo:
    host: str
    port: int


class DatabaseWrapper:
    # TODO different wrapper for admin, user, oracle
    def __init__(self, param_store) -> None:
        super().__init__()
        self._param_store: ParamStore = param_store

    def list_commits(self, label: str):
        return self._param_store.list_commits(label)


class _UserElementContext:
    def __init__(self, core: '_QuamCore') -> None:
        super().__init__()
        self.core = core


class _QuamCore:
    def __init__(self, path):
        if path is None:
            path = ".entropy"
        self.path = path
        os.makedirs(path, exist_ok=True)

        db_path = os.path.join(path, "params.db")
        self._param_store = ParamStoreConnector.connect(db_path)
        self._instruments_store = LabResources(SqlAlchemyDB(path))

        p = os.path.join(self.path, DEFAULT_COMMIT)
        commit = None
        if os.path.isfile(p):
            with open(p, "r") as f:
                commit = f.readline()
                commit = commit.strip()
        if commit is not None:
            self.checkout(commit_id=commit)

        self._initialize()

    def _initialize(self):
        if _ELEMENTS not in self._param_store:
            self._param_store[_ELEMENTS] = Munch()
        if _PARAMETERS not in self._param_store:
            self._param_store[_PARAMETERS] = Munch()

        self._parameters = _QuamParameters(self._param_store[_PARAMETERS], _UserElementContext(self))
        self._elements = _QuamElements(self._param_store[_ELEMENTS])

    @property
    def parameters(self):
        return self._parameters

    @property
    def elements(self):
        return self._elements

    @property
    def database(self):
        return self._param_store

    @property
    def instruments(self):
        return self._instruments_store

    def add(self, obj):
        # TODO check there's no element with the same name
        if isinstance(obj, ConfigBuilderElement):
            element_dict = _config_builder_to_dict(obj, obj.name)
            self._param_store[_ELEMENTS][element_dict["name"]] = element_dict
        else:
            raise ValueError(f"element of type {type(obj)} is not supported")

    def commit(self, label: str = None):
        # TODO should handle instruments as well?
        return self._param_store.commit(label)

    def checkout(
        self,
        commit_id: Optional[str] = None,
        commit_num: Optional[int] = None,
        move_by: Optional[int] = None,
    ):
        # TODO should handle instruments as well?
        self._param_store.checkout(
            commit_id=commit_id, commit_num=commit_num, move_by=move_by
        )
        # TODO check there's something there
        self._initialize()

    def merge(
        self,
        theirs: Union[Dict, ParamStore],
        merge_strategy: Optional[MergeStrategy] = MergeStrategy.OURS,
    ):
        self._param_store.merge(theirs, merge_strategy)

    def build_qua_config(self) -> ConfigBuilder:
        cb = ConfigBuilder()
        for v in self._elements.get_elements():
            cb_element = _dict_to_config_builder(v, self._parameters)
            if cb_element is not None:
                cb.add(cb_element)
        return cb

    def get_instruments(
        self,
        name,
        experiment_args: Optional[List] = None,
        experiment_kwargs: Optional[Dict] = None,
    ):
        return self._instruments_store.get_resource(
            name, experiment_args, experiment_kwargs
        )

    def set_instrument(self, name, resource_class, *args, **kwargs):
        if self._instruments_store.resource_exist(name):
            self._instruments_store.remove_resource(name)
            self._instruments_store.register_resource(
                name, resource_class, *args, **kwargs
            )
        else:
            self._instruments_store.register_resource(
                name, resource_class, *args, **kwargs
            )

    def remove_resource(self, name):
        self._instruments_store.remove_resource(name)

    def new_parameter(self, name, setter, **kwargs):
        # add both to the config builder vars, and save all info in quam
        self._parameters.parameter(name, setter, **kwargs)
        return {
            "type_cls": "UserParameter",
            "name": name,
        }

    def get_user_parameter(self, name):
        return self._parameters.get_config_var(name)

    def set_qop(self, arg, host, port):
        def _set_qop_info(_host, _port):
            _info = {"host": _host, "port": _port}
            self._param_store[f"{_QOP_INFO}/{_host}"] = _info

        if arg is not None:
            # should accept arg (enum/qmm) or named host and port
            if isinstance(arg, QuantumMachinesManager):
                _set_qop_info(arg._server_details.host, arg._server_details.port)
            elif isinstance(arg, QopInfo):
                _set_qop_info(arg.host, arg.port)
        elif host is not None and port is not None:
            _set_qop_info(host, port)
        else:
            raise ValueError("QOP info is not valid")

    def set_default_commit(self, commit_id):
        p = os.path.join(self.path, DEFAULT_COMMIT)
        with open(p, "w") as f:
            f.write(commit_id)

    def get_current_commit(self) -> str:
        return self._param_store.commit_id

    def execute_on_resource(self, info: FunctionInfo, *args, **kwargs):
        def hasmethod(obj, name):
            return hasattr(obj, name) and type(getattr(obj, name)) == MethodType

        res = self._instruments_store.get_resource(info.instrument_name)
        # TODO support multiple attrs?
        if hasmethod(res, info.function_name):
            attr = getattr(res, info.function_name)
            attr(*args, **kwargs)
        else:
            setattr(res, info.function_name, *args, **kwargs)
