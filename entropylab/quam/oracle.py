from cached_property import cached_property

from entropylab.quam.core import QuamBaseClass
from entropylab import LabResources, SqlAlchemyDB

from qm.QuantumMachinesManager import QuantumMachinesManager

class QuamOracle(QuamBaseClass):
    
    def __init__(self, path='.entropy') -> None:
        super().__init__(path)
        self._instrument_store = LabResources(SqlAlchemyDB(path))
        self.instrument_list = tuple(self._instrument_store.all_resources())

    def __repr__(self):
        return f"QuamOracle({self.path})"

    @property
    def element_names(self):
        return list(self.elements.keys())

    @property
    def QUA_element_names(self):
        return list(self.config_builder_objects.keys())

    def operations(self, elm_name: str):
        config = self.config
        if elm_name in config["elements"].keys():
            return list(config["elements"][elm_name]["operations"].keys())

    @property
    def user_params(self):
        return list(self.config_vars.params.keys())

    @property
    def integration_weights(self):
        return list(self.config["integration_weights"].keys())

    @cached_property
    def config(self):
        return self.build_qua_config()
