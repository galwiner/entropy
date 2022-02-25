from munch import Munch
import copy

from entropylab.quam.core import QuamBaseClass
from entropylab import LabResources, SqlAlchemyDB
from qm.QuantumMachinesManager import QuantumMachinesManager


class QuamUser(QuamBaseClass):
    
    def __init__(self, path='.entropy', host="127.0.0.1"):
        super().__init__(path)
        self.host = host
        self.elements = Munch()
        self.pulses = Munch()
        self.integration_weights = Munch()
        self._instrument_store = LabResources(SqlAlchemyDB(path))
        self.instrument_list = self._instrument_store.all_resources()
        self.qm_manager = QuantumMachinesManager(host)
        self.quantum_machine = None
        self._config = dict()

    def __repr__(self):
        return f"QuamUser({self.path})"

    @property
    def config(self):
        return self.build_qua_config()

    def execute_qua(self, prog, use_simulator=False, simulation_config=None):

        self.qm_manager.close_all_quantum_machines()
        
        if self._config != self.config or self.quantum_machine is None:
            self.quantum_machine = self.qm_manager.open(self.config)
                
        if use_simulator:
            job = self.quantum_machine.simulate(self.config, prog, simulation_config)
        else:
            job = self.quantum_machine.execute(self.config, prog, simulation_config)
        job.result_handles.wait_for_all_values()
        return job

    def load(self, c_id):
        super().load(c_id)
        config = self.config
        self._config = copy.deepcopy(config)
        for elm in config["elements"].keys():
            self.elements[elm] = elm
        for elm in config["pulses"].keys():
            self.pulses[elm] = elm
        for elm in config["integration_weights"].keys():
            self.integration_weights[elm] = elm
