from cached_property import cached_property
from munch import Munch

from entropylab.quam.core import QuamBaseClass, QMInstrument
from entropylab import LabResources, SqlAlchemyDB

from qm.QuantumMachinesManager import QuantumMachinesManager

class QuamOracle(QuamBaseClass, Munch):
    
    def __init__(self, path='.entropy') -> None:
        super().__init__(path).__init__()
        self._instrument_store = LabResources(SqlAlchemyDB(path))
        self.instrument_list = tuple(self._instrument_store.all_resources())
        self.user_params = []
        self.quantum_machine_names = []

    def __repr__(self):
        return f"QuamOracle({self.path})"

    def load(self, c_id):
        super().load(c_id)
        self.set_config_vars()
        self.user_params = list(self.config_vars.params.keys())
        for (k,v) in self.instruments.items():
            self.quantum_machine_names.append(k)
            v.build_qua_config()
            self[k] = Munch()
            self[k]["elements"] = list(v.config["elements"].keys())
            self[k]["pulses"] = list(v.config["pulses"].keys())
            self[k]["integration_weights"] = list(v.config["integration_weights"].keys())
            self[k]["operations"] = Munch()
            for e in self[k].elements:
                self[k].operations[e] = list(v.config["elements"][e]["operations"].keys())