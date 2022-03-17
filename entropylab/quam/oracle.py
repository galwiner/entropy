from typing import Optional

from cached_property import cached_property

from entropylab.quam.core import _QuamCore, DatabaseWrapper


class QuamOracle:
    def __init__(self, path) -> None:
        super().__init__()
        if isinstance(path, _QuamCore):
            self._core = path
        else:
            self._core = _QuamCore(path)

    def __repr__(self):
        return f"QuamOracle({self._core.path})"

    @property
    def element_names(self):
        return self._core.elements.get_names()

    def operations(self, elm_name: str):
        config = self.config
        if elm_name in config["elements"].keys():
            return list(config["elements"][elm_name]["operations"].keys())

    @property
    def user_params(self):
        return list(self._core.parameters.get_names())

    @property
    def integration_weights(self):
        return list(self.config["integration_weights"].keys())

    @cached_property
    def config(self):
        return self._core.build_qua_config().build()

    def checkout(
        self,
        commit_id: Optional[str] = None,
            commit_num: Optional[int] = None,
            move_by: Optional[int] = None,
    ):
        return self._core.checkout(
            commit_id=commit_id, commit_num=commit_num, move_by=move_by
        )

    @property
    def database(self) -> DatabaseWrapper:
        return DatabaseWrapper(self._core.database)

    @property
    def commit_id(self):
        return self._core.get_current_commit()
