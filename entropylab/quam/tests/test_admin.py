from qm.qua import *
from entropylab.quam.admin import QuamAdmin
from qualang_tools.config.components import *



def test_resonator_spectroscopy():
    # 1d scan without external devices
    # Configure a machine able to run resonator spectroscopy as admin

    admin, quam, oracle = quam_init()
    cont = Controller('cont1',n_analog_outputs=10,n_analog_inputs=2,n_digital_outputs=10,controller_type='opx1')
    controller_name = 'cont1'
    admin.add(QuaElement(name,type=QCONTROLLERS.OPXPlus))

    
    admin.add(user_parameter('xmon_if', default=1e6,persistent = False))
    admin.add(user_parameter('xmon_lo'))
    admin.add(user_parameter('ror_if'))
    admin.add(user_parameter('ro_amp'))
    admin.add(user_parameter('ro_duration'))
    admin.add(user_parameter('pi_wf_samples'))

    xmon = Transmon(name='xmon', I=admin.cont1.analog_output(2), Q=admin.cont1.analog_output(3),
                    intermediate_frequency=admin.params.xmon_if)

    xmon.mixer = Mixer(name='xmon_mixer', intermediate_frequency=admin.params.xmon_if,
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

    # Run a resonator spectroscopy as a user
    #assert oracle.get_elements
    assert oracle.get_QUA_elements == ['ror', 'xmon']
    assert oracle.get_operations('ror') == ['readout_pulse']
    assert oracle.get_iw == ['w1', 'w2']
    assert oracle.get_user_params == ['ro_amp', 'ro_duration', 'xmon_if', 'xmon_lo', 'ror_if']

    # User

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


