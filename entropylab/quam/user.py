from munch import Munch

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

    def __repr__(self):
        return f"QuamUser({self.path})"

    @property
    def config(self):
        return self.build_qua_config()

    def execute_qua(self, prog, use_simulator=False, simulation_config=None):
        qmm = QuantumMachinesManager(host=self.host)
        qmm.close_all_quantum_machines()
        if use_simulator:
            job = qmm.simulate(self.config, prog, simulation_config)
        else:
            job = qmm.execute(self.config, prog, simulation_config)
        job.result_handles.wait_for_all_values()
        return job

    def load(self, c_id):
        super().load(c_id)
        config = self.config
        for elm in config["elements"].keys():
            self.elements[elm] = elm
        for elm in config["pulses"].keys():
            self.pulses[elm] = elm
        for elm in config["integration_weights"].keys():
            self.integration_weights[elm] = elm
