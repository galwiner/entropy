from qm.qua import *
from entropylab.quam.admin import QuamAdmin, quam_init, QuamElement, QuamTransmon, \
    QuamReadoutResonator, QuamController
from qualang_tools.config.components import *
from entropylab.quam.dummy_driver import DummyInst, DummyDC
import numpy as np
from qm import SimulationConfig


def test_flux_tunable_qubit():
    path = 'tests_cache/.entropy'
    admin, quam, oracle = quam_init(path)

    def test_admin(admin):
        admin.set_instrument(name='flux_driver', resource_class=DummyDC)

        def flux_setter(value):
            admin.instruments.flux_driver.v1 = value

        cont = QuamController(name='cont1')

        class QuamFluxTunableXmon(QuamTransmon):
            def __init__(self, flux_channel, **kwargs):
                super().__init__(**kwargs)
                self.flux_channel = flux_channel

        xmon = QuamFluxTunableXmon(name='xmon', I=cont.analog_output(1), Q=cont.analog_output(2),
                                   flux_channel=admin.inst_vars.parameter('flux_driver', setter=flux_setter),
                                   intermediate_frequency=admin.config_vars.parameter("xmon_if"))

        xmon.lo_frequency = admin.config_vars.parameter("xmon_lo")

        xmon.mixer = Mixer(name='xmon_mixer',
                           intermediate_frequency=admin.config_vars.parameter("xmon_if"),
                           lo_frequency=admin.config_vars.parameter("xmon_lo"),
                           correction=Matrix2x2([[1, 0], [0, 1]]))

        admin.add(xmon)

        admin.save()
        commit_id = admin.commit("set config vars")
        # print(commit_id)
        admin.params.checkout(commit_id)  # checking we can also checkout from the ParamStore
        return commit_id  # this is a temporary solution for communicating between the three interfaces

    def test_quam(quam, c_id):
        quam.load(c_id)
        # user sets some parameters
        quam.params.xmon_lo = 1e9
        quam.params.xmon_if = 1e6
        quam.params.ror_if = 1e6
        quam.params.ror_amp = 0.5
        quam.params.ro_duration = 1000
    #
    # quam.xmon.flux = 12
    #
        with program() as prog:
            f = declare(int)
            I = declare(fixed)
            Q = declare(fixed)
            I_str = declare_stream()
            Q_str = declare_stream()
            with for_(f, f_start, f < f_end, f + df):

                quam.qua_executor.wait_for_external(quam.xmon1.set_flux, (x for x in range(f_start, f_end, df)),
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
