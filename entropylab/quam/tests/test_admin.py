from qm.qua import *
from entropylab.quam.admin import QuamAdmin, quam_init, QuaElement, QCONTROLLERS,Transmon
from qualang_tools.config import components as qua_components




def test_resonator_spectroscopy():
    
    # 1d scan without external devices
    # Configure a machine able to run resonator spectroscopy as admin
    path = 'tests_cache/quam_db.db'
    admin, quam, oracle = quam_init(path)
    def admin_scope(admin):
    
        controller_name = 'cont1'
        cont = qua_components.Controller(controller_name)
        
        admin.add_parameter('xmon_if', default=1e6,persistent = False))
        
        admin.add(Transmon('xmon', I=cont.analog_output(1), Q=cont.analog_output(2),
                        intermediate_frequency=admin.params.xmon_if))
        
        
        # admin.add(user_parameter('xmon_if', default=1e6,persistent = False))
        # admin.add(user_parameter('xmon_lo'))
        # admin.add(user_parameter('ror_if'))
        # admin.add(user_parameter('ro_amp'))
        # admin.add(user_parameter('ro_duration'))
        # admin.add(user_parameter('pi_wf_samples'))

        xmon = Transmon(name='xmon', I=admin.cont1.analog_output(2), Q=admin.cont1.analog_output(3),
                        intermediate_frequency=admin.params.xmon_if)

        xmon.mixer = qua_components.Mixer(name='xmon_mixer', intermediate_frequency=admin.params.xmon_if,
                        lo_frequency=admin.params.xmon_lo,
                        correction=Matrix2x2([[1, 0], [0, 1]]))  # TODO: add default correction matrix

        admin.backend.cont1.add(ArbitraryWaveform('wf_ramp', np.linspace(-0.5, 0.5, 1000)))
        admin.cont1.add(ConstantWaveform('wf_zero', 0))
        admin.cont1.add(ConstantWaveform('readout_wf', admin.params.ro_amp))
        admin.cont1.add(ArbitraryWaveform('pi_wf_opt', admin.params.pi_wf_samples))


        xmon.add(Operation(ControlPulse("pi_pulse", [admin.cont1.wf_ramp, admin.cont1.wf_zero], 1000)))
        xmon.add(Operation(ControlPulse("opt_pi_pulse", [admin.cont1.pi_wf_opt, admin.cont1.wf_zero], 1000)))

        admin.add(xmon)
        const_wf = ConstantWaveform('wf_zero', 0)
        ror = ReadoutResonator('ror', [admin.cont1.analog_output(4), admin.cont1.analog_output(5)],
                            [admin.cont1.analog_input(1), admin.cont1.analog_input(2)],
                            intermediate_frequency=admin.params.ror_if)
        ror.mixer = Mixer(name='ror_mixer', intermediate_frequency=admin.params.ror_if, lo_frequency=admin.params.ror_lo,
                        correction=Matrix2x2([[1, 0], [0, 1]]))  # TODO: add default correction matrix
        ror.add(Operation(MeasurePulse('readout_pulse', [admin.readout_wf, admin.zero_wf], admin.params.ro_duration)))

        admin.add(ror)

        admin.add(IntegrationWeights('w1', cosine=[1], sine=[0]))
        admin.add(IntegrationWeights('w2', cosine=[0], sine=[1]))
    def oracle_scope(oracle):
        # Run a resonator spectroscopy as a user
        #assert oracle.get_elements
        assert oracle.get_QUA_elements == ['ror', 'xmon']
        assert oracle.get_operations('ror') == ['readout_pulse']
        assert oracle.get_iw == ['w1', 'w2']
        assert oracle.get_user_params == ['ro_amp', 'ro_duration', 'xmon_if', 'xmon_lo', 'ror_if']

    # User
    def user_scope(quam):
        quam.params.xmon_lo = 1e9
        quam.params.xmon_if = 1e6
        quam.params.ror_if = 1e6
        quam.params.ror_amp = 0.5
        quam.params.ror_duration = 1000

        f_start = int(10e6)
        f_end = int(50e6)
        df = int(1e6)

        with program() as prog:
            f = declare(int)
            I = declare(fixed)
            Q = declare(fixed)
            I_str = declare_stream()
            Q_str = declare_stream()
            with for_(f, f_start, f < f_end, f + df):
                update_frequency(quam.ror, f)
                measure(quam.ror.readout_pulse, quam.ror, None, demod.full(quam.w1, I), demod.full(quam.w2, Q))
                save(I, I_str)
                save(Q, Q_str)
            with stream_processing():
                I_str.save_all('I_out')
                Q_str.save_all('Q_out')

        quam.qua_executor.run(prog)

        assert quam.qua_executor.results('last').names == ['I_out', 'Q_out']

    admin_scope(admin)
    oracle_scope(oracle)
    user_scope(quam)

# def test_flux_tunable_qubit():

#     admin, quam, oracle = quam_init(path='.', load_existing=True)

#     #driverStore is a collection of drivers that is external to Quam. TODO: decide where it should exist and how it is to be maintained
#     #QuAM remembers the driver class and args

#     admin.add_device(name="flux_driver", driverStore.dc.QDAC2('COM1'))

#     admin.add_user_parameter('flux_idle')
#     admin.add_user_parameter('flux_offset')
#     #ConfigBuilder object needs to be able to be combined with other instruments
#     xmon = FluxTunableTransmon(name='xmon1', I=admin.cont1.analog_output(2), Q=admin.cont1.analog_output(3),
#                                fl_port=admin.con1.analog_port(4, offset=admin.params.flux_offset),
#                                intermediate_frequency=admin.params.xmon_if)

#     xmon.mixer = Mixer(name='xmon_mixer', intermediate_frequency=admin.params.xmon_if,
#                        lo_frequency=admin.params.xmon_lo,
#                        correction=Matrix2x2([[1, 0], [0, 1]]))  # TODO: add default correction matrix

#     admin.cont1.add(ArbitraryWaveform('wf_ramp', np.linspace(-0.5, 0.5, 1000)))

#     xmon.add(Operation(ControlPulse("pi_pulse", [admin.cont1.wf_ramp, admin.cont1.wf_zero], 1000)))

#     xmon.add(Operation(ControlPulse("fluxPulse", [admin.cont1.flux_idle], 1000)))

#     #xmon.add(NativeGate('X'))
#     #quam.xmon1.gates.X -> play, play
#     #quam.xmon2.gates.Y -> play, play
#     #play()

#     admin.cont1.add(xmon)

#     ror = ReadoutResonator('xmon_ror', [admin.cont1.analog_output(4), admin.cont1.analog_output(5)],
#                            [admin.cont1.analog_input(1), admin.cont1.analog_input(2)],
#                            intermediate_frequency=admin.params.ror_if)
#     ror.mixer = Mixer(name='ror_mixer', intermediate_frequency=admin.params.ror_if, lo_frequency=admin.params.ror_lo,
#                       correction=Matrix2x2([[1, 0], [0, 1]]))  # TODO: add default correction matrix

#     # user side

#     quam.xmon.flux = 12 


#     with program() as prog:
#         f = declare(int)
#         I = declare(fixed)
#         Q = declare(fixed)
#         I_str = declare_stream()
#         Q_str = declare_stream()
#         with for_(f, f_start, f < f_end, f + df):
#             #the external function call values can be passed via python or via some IO variable trick. TODO: verify design
#             quam.qua_executor.wait_for_external(quam.xmon1.set_flux,(x for x in range(f_start,f_end,df)), interval_wait=0.1)


#             update_frequency(quam.ror, f)
#             measure(quam.ror.readout_pulse, quam.ror, None, demod.full(quam.w1, I), demod.full(quam.w2, Q))
#             save(I, I_str)
#             save(Q, Q_str)
#         with stream_processing():
#             I_str.save_all('I_out')
#             Q_str.save_all('Q_out')

#     quam.qua_executor.run(prog)

test_resonator_spectroscopy()