from qm.qua import *
from entropylab.quam.admin import QuamAdmin, QMInstrument
from entropylab.quam.core import QuamElement
from entropylab.quam.initialization import quam_init

from qualang_tools.config.components import *
from entropylab.quam.dummy_driver import DummyInst
import numpy as np
from qm import SimulationConfig

from qualang_tools.config import components as qua_components
import os, sys

sys.path.append(os.path.abspath(os.getcwd()))
## this line is needed to make the Quam objects defined below to be accessible in the global scope
## for pickling and unpickling QuamElements to param store

cb_objs = ["Controller", "Transmon", "ReadoutResonator"]
for obj in cb_objs:
    globals()["Quam" + obj] = type("Quam" + obj, (QuamElement, getattr(qua_components, obj)), {})

def test_resonator_spectroscopy_separated():

    path = 'entropylab/quam/tests/tests_cache'
    admin, quam, oracle = quam_init(path)

    def test_admin(admin):
        admin.set_instrument(name='qm', resource_class=QMInstrument)

        cont = QuamController(name='cont1')

        admin.qm.add(cont)

        xmon = QuamTransmon(name='xmon', I=cont.analog_output(1), Q=cont.analog_output(2),
                            intermediate_frequency=admin.config_vars.parameter("xmon_if"))

        xmon.lo_frequency = admin.config_vars.parameter("xmon_lo")

        xmon.mixer = Mixer(name='xmon_mixer', 
                           intermediate_frequency=admin.config_vars.parameter("xmon_if"),
                           lo_frequency=admin.config_vars.parameter("xmon_lo"),
                           correction=Matrix2x2([[1, 0], [0, 1]]))

        zero_wf = ConstantWaveform('wf_zero', 0)

        xmon.add(Operation(ControlPulse("pi_pulse",
                                        [ArbitraryWaveform('wf_ramp', list(np.linspace(-0.5, 0.5, 1000))),
                                         zero_wf],
                                        1000)))
        
        xmon.add(Operation(ControlPulse("opt_pi_pulse",
                                        [ArbitraryWaveform('pi_wf_opt', admin.config_vars.parameter("pi_wf_samples")),
                                         zero_wf],
                                        1000)))

        admin.qm.add(xmon)

        ror = QuamReadoutResonator(name='ror',
                                   inputs=[cont.analog_output(4), cont.analog_output(5)],
                                   outputs=[cont.analog_input(1), cont.analog_input(2)],
                                   intermediate_frequency=admin.config_vars.parameter("ror_if"))
        ror.lo_frequency = admin.config_vars.parameter("ror_lo")
        ror.mixer = Mixer(name='ror_mixer', 
                          intermediate_frequency=admin.config_vars.parameter("ror_if"),
                          lo_frequency=admin.config_vars.parameter("ror_lo"),
                          correction=Matrix2x2([[1, 0], [0, 1]]))  # TODO: add default correction matrix
        ro_pulse = MeasurePulse('readout_pulse',
                                [ConstantWaveform('readout_wf', admin.config_vars.parameter("ro_amp")),
                                 zero_wf],
                                admin.config_vars.parameter("ro_duration"))
        ro_pulse.add(Weights(ConstantIntegrationWeights('w1', cosine=1, sine=0, 
                                                        duration = admin.config_vars.parameter("ro_duration"))))
        ro_pulse.add(Weights(ConstantIntegrationWeights('w2', cosine=0, sine=1,
                                                        duration = admin.config_vars.parameter("ro_duration"))))
        ror.add(Operation(ro_pulse))
        ror.time_of_flight = 24
        admin.qm.add(ror)

        #admin sets some default values just to test himself and see a config can be built.

        admin.params['xmon_if'] = 10e6
        admin.params['xmon_lo'] = 10e6
        admin.params['pi_wf_samples'] = list(np.random.rand(1000))
        admin.params['ror_if'] = 1e6
        admin.params['ror_lo'] = 1e6
        admin.params['ro_amp'] = 1e-2
        admin.params['ro_duration'] = 200e-9

        admin.build_qua_configurations() #TODO: add a test that the built config is correct
        commit_id = admin.commit("set config vars")
        #print(commit_id)
        admin.params.checkout(commit_id) #checking we can also checkout from the ParamStore
        return commit_id


    def test_oracle(oracle, c_id):
        # Run a resonator spectroscopy as a user
        oracle.load(c_id)
        assert set(oracle.element_names) == set(['cont1', 'xmon', 'ror']) #element can be non qua elements. maybe we need to rename. maybe this should be seperate from qua
        assert set(oracle.QUA_element_names) == set(['cont1','ror', 'xmon'])
        commit_list = oracle.params.list_commits('set config vars')
        oracle.params.checkout(c_id)# make sure checkout from the oracle is possible.
        assert oracle.operations('ror') == ['readout_pulse']
        assert oracle.integration_weights == ['w1', 'w2']
        assert set(oracle.user_params) == set(['pi_wf_samples','ro_amp', 'ro_duration', 'xmon_if', 'xmon_lo', 'ror_if', 'ror_lo'])
        return c_id
    # User
    def test_quam(quam, c_id):
        quam.load(c_id)
        # user sets some parameters
        quam.params.xmon_lo = 1e9
        quam.params.xmon_if = 1e6
        quam.params.ror_if = 1e6
        quam.params.ror_amp = 0.5
        quam.params.ro_duration = 1000
        
        c_id = quam.commit(label='update config vars') #user is able to commit to param store
        f_start = int(10e6)
        f_end = int(50e6)
        df = int(1e6)
        # quam.xmon.flux = 1  # in MHz

        with program() as prog:
            f = declare(int)
            I = declare(fixed)
            Q = declare(fixed)
            I_str = declare_stream()
            Q_str = declare_stream()
            with for_(f, f_start, f < f_end, f + df):
                update_frequency(quam.elements.ror, f)
                measure(quam.pulses.readout_pulse, quam.elements.ror, None, 
                        demod.full(quam.integration_weights.w1, I, "out1"),
                        demod.full(quam.integration_weights.w2, Q, "out2"))
                save(I, I_str)
                save(Q, Q_str)
            with stream_processing():
                I_str.save_all('I_out')
                Q_str.save_all('Q_out')
      
        res = quam.execute_qua(prog, 
                               simulation_config=SimulationConfig(duration=10000),
                               use_simulator=True)
        assert hasattr(res.result_handles, 'I_out')
        assert hasattr(res.result_handles, 'Q_out')

    c_id = test_admin(admin)
    c_id = test_oracle(oracle, c_id)
    test_quam(quam, c_id)

    assert True

test_resonator_spectroscopy_separated()



