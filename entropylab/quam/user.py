from munch import Munch
import copy

from entropylab.quam.core import QuamBaseClass, QMInstrument
from entropylab import LabResources, SqlAlchemyDB
from qm.QuantumMachinesManager import QuantumMachinesManager


class QuamUser(QuamBaseClass, Munch):
    
    def __init__(self, path='.entropy', host="127.0.0.1"):
        super().__init__(path).__init__()
        self.host = host
        self._instrument_store = LabResources(SqlAlchemyDB(path))
        self.instrument_list = self._instrument_store.all_resources()
        self.qm_manager = QuantumMachinesManager(host)
        self.quantum_machines = dict()

    def __repr__(self):
        return f"QuamUser({self.path})"

    def load(self, c_id):
        super().load(c_id)
        self.set_config_vars()
        self.set_config_data()

    def commit(self, label: str):
        self.set_config_vars()
        super().commit(label)
      
    def set_config_data(self):
        for (k,v) in self.instruments.items():
            if isinstance(v, QMInstrument):
                v.build()
                self[k] = v
                self[k].qm_manager = self.qm_manager.open_qm(v.config)
                self[k].host = self.host
                self[k]["elements"] = Munch()
                for e in v.config["elements"].keys():
                    self[k].elements[e] = e     
                self[k]["pulses"] = Munch()
                for e in v.config["pulses"].keys():
                    self[k].pulses[e] = e
                self[k]["integration_weights"] = Munch()
                for e in v.config["integration_weights"].keys():
                    self[k].integration_weights[e] = e
