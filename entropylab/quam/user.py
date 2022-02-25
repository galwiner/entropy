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


    def execute_qua(self, qm, prog, use_simulator=False, simulation_config=None):
        #self.qm_manager.close_all_quantum_machines()
        self.set_config_vars()
        config = copy.deepcopy(self.instruments[qm].config)
        self.instruments[qm].build_qua_config()
        if config != self.instruments[qm].config:
            config = self.instruments[qm].config
            self.quantum_machines[qm] = self.qm_manager.open_qm(config)      
        if use_simulator:
            job = self.quantum_machines[qm].simulate(prog, simulation_config)
        else:
            job = self.quantum_machines[qm].execute(prog, simulation_config)
        job.result_handles.wait_for_all_values()
        return job

    def load(self, c_id):
        super().load(c_id)
        self.set_config_vars()
        self.set_config_data()
        self.set_quantum_machines()

    def set_quantum_machines(self):
        for (k,v) in self.instruments.items(): 
            if isinstance(v, QMInstrument):
                self.quantum_machines[k] = self.qm_manager.open_qm(v.config)

    def set_config_data(self):
        for (k,v) in self.instruments.items():
            if isinstance(v, QMInstrument):
                v.build_qua_config()
                self[k] = Munch()
                self[k]["elements"] = Munch()
                for e in v.config["elements"].keys():
                    self[k].elements[e] = e     
                self[k]["pulses"] = Munch()
                for e in v.config["pulses"].keys():
                    self[k].pulses[e] = e
                self[k]["integration_weights"] = Munch()
                for e in v.config["integration_weights"].keys():
                    self[k].integration_weights[e] = e
