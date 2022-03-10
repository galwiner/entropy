from typing import Optional

from munch import Munch
from qm.QuantumMachinesManager import QuantumMachinesManager

from entropylab.quam.core import _QuamCore, _QOP_INFO, DatabaseWrapper
from entropylab.quam.quam_components import Parameter, _QuamElements


class _QuamUserUtils:
    def __init__(self, path):
        super().__init__()
        self._core = _QuamCore(path)
        # TODO load on latest by default?
        try:
            self.checkout(move_by=0)
        except BaseException:
            pass

        try:
            qop_info = self._core._param_store.get(_QOP_INFO)
            self._qmm = QuantumMachinesManager(
                host=qop_info["host"], port=qop_info["port"]
            )
        except BaseException:
            self._qmm = None

    @property
    def config(self):
        return self._core.build_qua_config().build()

    @property
    def elements(self) -> _QuamElements:
        return self._core.elements

    def checkout(
        self,
        commit_id: Optional[str] = None,
        commit_num: Optional[int] = None,
        move_by: Optional[int] = None,
    ):
        self._core.checkout(commit_id, commit_num, move_by)
        # config = self.config
        # for elm in config["elements"].keys():
        #     self.elements[elm] = elm
        # for elm in config["pulses"].keys():
        #     self.pulses[elm] = elm
        # for elm in config["integration_weights"].keys():
        #     self.integration_weights[elm] = elm

    def execute_qua(self, prog, use_simulator=False, simulation_config=None):
        if self._qmm is None:
            raise ValueError("QOP address is not defined")
        self._qmm.close_all_quantum_machines()
        if use_simulator:
            job = self._qmm.simulate(self.config, prog, simulation_config)
        else:
            qm = self._qmm.open_qm(self.config)
            job = qm.execute(self.config, prog)
        job.result_handles.wait_for_all_values()
        return job

    @property
    def database(self) -> DatabaseWrapper:
        return DatabaseWrapper(self._core.database)

    def commit(self, label):
        return self._core.commit(label)


class _UserElementAccess(Munch):
    is_frozen = False

    def __init__(self, element, context) -> None:
        super().__init__()
        self._element = element
        self._context: _QuamUserUtils = context
        self.is_frozen = True

    def __getattr__(self, item):
        # TODO - add here a real wrapper for auto complete
        if self.is_frozen and hasattr(self._element, item):
            return _UserElementAccess(getattr(self._element, item), self._context)
        else:
            try:
                object.__getattribute__(self, item)
            except:
                raise AttributeError(f"attribute {item} is not found")

    def __setattr__(self, item, value):
        if self.is_frozen and item in self._element:
            attr = self._element[item]
            if (
                isinstance(attr, dict)
                and "type_cls" in attr
                and attr["type_cls"] == "UserParameter"
            ):
                param: Parameter = self._context._core.get_user_parameter(
                    name=attr["name"]
                )
                param.set_value(value)
            else:
                raise AttributeError(f"quam user can not set attribute {item} value")
        else:
            object.__setattr__(self, item, value)


class QuamUser:
    def __init__(self, path) -> None:
        super().__init__()
        self.utils = _QuamUserUtils(path)

    def __repr__(self):
        return f"QuamUser({self._core.path})"

    def __getattr__(self, item):
        return _UserElementAccess(self.utils.elements.get(item), self.utils)
