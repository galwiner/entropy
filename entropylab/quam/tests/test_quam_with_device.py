from qm.qua import *
from entropylab.quam.admin import QuamAdmin
from entropylab.quam.initialization import quam_init
from entropylab.quam.core import QuamElement, QMInstrument
from qualang_tools.config.components import *
from entropylab.quam.dummy_driver import DummyInst, DummyDC
import numpy as np
from qm import SimulationConfig


from qualang_tools.config import components as qua_components
import os, sys

sys.path.append(os.path.abspath(os.getcwd()))

cb_objs = ["Controller", "Transmon", "ReadoutResonator"]
for obj in cb_objs:
    globals()["Quam" + obj] = type("Quam" + obj, (QuamElement, getattr(qua_components, obj)), {})

class QuamFluxTunableXmon(qua_components.Transmon, QuamElement):
    def __init__(self, flux_channel, *args, **kwargs):
        self.flux_channel = flux_channel
        super().__init__(*args, **kwargs)

def test_flux_tunable_qubit():
    path=os.path.join(os.getcwd(), 'tests_cache')
    #path = 'entropylab/quam/tests/tests_cache/'
    admin, quam, oracle = quam_init(path)

    def test_admin(admin):
        admin.remove_all_instruments()
        admin.set_instrument(name='flux_driver', resource_class=DummyDC, args=["flux_driver"])
        admin.set_instrument(name='qm', resource_class=QMInstrument)
        def flux_setter(value):
            admin.instruments.flux_driver.v1 = value

        ##xmon.flux_channel(30)
        cont = QuamController(name='con1')
        admin.qm.add(cont)
        xmon = QuamFluxTunableXmon(name='xmon', I=cont.analog_output(1), Q=cont.analog_output(2),
                                   flux_channel=admin.config_vars.parameter('flux_driver', setter=flux_setter),
                                   intermediate_frequency=admin.config_vars.parameter("xmon_if"))

        xmon.lo_frequency = admin.config_vars.parameter("xmon_lo")

        xmon.mixer = Mixer(name='xmon_mixer',
                           intermediate_frequency=admin.config_vars.parameter("xmon_if"),
                           lo_frequency=admin.config_vars.parameter("xmon_lo"),
                           correction=Matrix2x2([[1, 0], [0, 1]]))

        admin.qm.add(xmon)

        zero_wf = ConstantWaveform('wf_zero', 0)
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

        admin.params['xmon_if'] = 10e6
        admin.params['xmon_lo'] = 10e6
        admin.params['pi_wf_samples'] = list(np.random.rand(1000))
        admin.params['ror_if'] = 1e6
        admin.params['ror_lo'] = 1e6
        admin.params['ro_amp'] = 1e-2
        admin.params['ro_duration'] = 200e-9
        #config = admin.build_qua_config()
        admin.config_vars.parameter("flux_driver")(12)
        assert admin.instruments.flux_driver.v1 == 12
        commit_id = admin.commit("set config vars")
        print(commit_id)
        
        admin.params.checkout(commit_id)  # checking we can also checkout from the ParamStore
        return commit_id  # this is a temporary solution for communicating between the three interfaces

    def test_oracle(oracle,c_id):
        oracle.load(c_id)
        assert set(oracle.instrument_list) == set(['flux_driver', 'qm'])  # element
        ##more tests?
        return c_id

    def test_quam(quam, c_id):
        quam.load(c_id)
        # user sets some parameters
        quam.params.xmon_lo = 1e9
        quam.params.xmon_if = 1e6
        quam.params.ror_if = 1e6
        quam.params.ror_amp = 0.5
        quam.params.ro_duration = 1000

        print("quam flux channel setter")
        print(quam.instruments["qm"].config_builder_objects["xmon"].flux_channel(12))
        print(quam.config_vars.parameter("flux_driver")())
    #
        #quam.elements.xmon.flux_channel(12)
        # quam.inst_vars.flux_sweep.setup_sweep(start,stop,duration) #sets up an instrument
        #quam.xmon.flux_channel

        quam.xmon.flux_channel.flux = 100
        quam.commit("flux sweep")
        f_start = 10.0
        f_end = 20.0
        df = 5.0
    #
        with program() as prog:
            f = declare(int)
            I = declare(fixed)
            Q = declare(fixed)
            I_str = declare_stream()
            Q_str = declare_stream()
            with for_(f, f_start, f < f_end, f + df):

                quam.qua_executor.wait_for_external(quam.xmon.set_flux, (x for x in range(f_start, f_end, df)),
                                                    interval_wait=0.1)

                update_frequency(quam.ror, f)
                measure(quam.ror.readout_pulse, quam.ror, None, demod.full(quam.w1, I), demod.full(quam.w2, Q))
                save(I, I_str)
                save(Q, Q_str)
            with stream_processing():
                I_str.save_all('I_out')
                Q_str.save_all('Q_out')
        #
    # quam.qua_executor.run(prog)
    c_id = test_admin(admin)
    c_id = test_oracle(oracle, c_id)
    test_quam(quam, c_id)

    assert True


test_flux_tunable_qubit()
    # admin.cont1.add(ArbitraryWaveform('wf_ramp', np.linspace(-0.5, 0.5, 1000)))
    #
    # xmon.add(Operation(ControlPulse("pi_pulse", [admin.cont1.wf_ramp, admin.cont1.wf_zero], 1000)))
    #
    # xmon.add(Operation(ControlPulse("fluxPulse", [admin.cont1.flux_idle], 1000)))
    #
    # # xmon.add(NativeGate('X'))
    # # quam.xmon1.gates.X -> play, play
    # # quam.xmon2.gates.Y -> play, play
    # # play()
    #
    # admin.cont1.add(xmon)
    #
    # ror = ReadoutResonator('xmon_ror', [admin.cont1.analog_output(4), admin.cont1.analog_output(5)],
    #                        [admin.cont1.analog_input(1), admin.cont1.analog_input(2)],
    #                        intermediate_frequency=admin.params.ror_if)
    # ror.mixer = Mixer(name='ror_mixer', intermediate_frequency=admin.params.ror_if, lo_frequency=admin.params.ror_lo,
    #                   correction=Matrix2x2([[1, 0], [0, 1]]))  # TODO: add default correction matrix
    #
