from qm.qua import *
from entropylab.quam.admin import QuamAdmin, quam_init, QuamElement, QuamTransmon,\
                                  QuamReadoutResonator, QuamController
from qualang_tools.config.components import *
from entropylab.quam.dummy_driver import DummyInst
import numpy as np
from qm import SimulationConfig


def test_resonator_spectroscopy_separated():

    path = 'tests_cache/quam_db.db'
    admin, quam, oracle = quam_init(path)

    def test_admin(admin):

        cont = QuamController(name='cont1')

        #admin.add_parameter('xmon_if', val=1e6, persistent=True)
        admin.add(cont)

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

        admin.add(xmon)

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
        admin.add(ror)

        #admin sets some default values just to test himself and see a config can be built.

        admin.params['xmon_if'] = 10e6
        admin.params['xmon_lo'] = 10e6
        admin.params['pi_wf_samples'] = list(np.random.rand(1000))
        admin.params['ror_if'] = 1e6
        admin.params['ror_lo'] = 1e6
        admin.params['ro_amp'] = 1e-2
        admin.params['ro_duration'] = 200e-9

        #print(admin._paramStore._params)
        config = admin.build_qua_config() #TODO: add a test that the built config is correct
        #print(config["integration_weights"])
        commit_id = admin.commit("set config vars")
        #print(commit_id)
        admin.params.checkout(commit_id) #checking we can also checkout from the ParamStore

        return admin.elements, admin.config_builder_objects, admin.config_vars, commit_id #this is a temporary solution for communicating between the three interfaces


    def test_oracle(oracle, elements, config_objects, config_vars, c_id):

        #these three lines will be automatic when the communication mechanism is done
        oracle.elements = elements
        oracle.config_builder_objects = config_objects
        oracle.config_vars = config_vars


        # Run a resonator spectroscopy as a user
        assert set(oracle.element_names) == set(['cont1', 'xmon', 'ror']) #element can be non qua elements. maybe we need to rename. maybe this should be seperate from qua
        assert set(oracle.QUA_element_names) == set(['cont1','ror', 'xmon'])
        commit_list = oracle.params.list_commits('set config vars')
        oracle.params.checkout(c_id)# make sure checkout from the oracle is possible.

        assert oracle.operations('ror') == ['readout_pulse']
        assert oracle.integration_weights == ['w1', 'w2']
        assert set(oracle.user_params) == set(['pi_wf_samples','ro_amp', 'ro_duration', 'xmon_if', 'xmon_lo', 'ror_if', 'ror_lo'])
        return oracle.elements, oracle.config_builder_objects, oracle.config_vars, c_id #this is a temporary solution for communicating between the three interfaces
    # User
    def test_quam(quam, elements, config_objects, config_vars, c_id):

        #these three lines will be automatic when the communication mechanism is done
        quam.elements = elements
        quam.config_builder_objects = config_objects
        quam.config_vars = config_vars

        # user sets some parameters
        quam.params.xmon_lo = 1e9
        quam.params.xmon_if = 1e6
        quam.params.ror_if = 1e6
        quam.params.ror_amp = 0.5
        quam.params.ro_duration = 1000

        c_id = quam.commit(label='update config vars') #user is able to commit to param store
        quam.params.checkout(c_id) #not necessary but shows that checkout is possible

        #print(quam.config)

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
                update_frequency("ror", f)
                measure("readout_pulse", "ror", None, 
                        demod.full("w1", I, "out1"), demod.full("w2", Q, "out2"))
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
        
    elements, config_objects, config_vars, c_id = test_admin(admin)
    elements, config_objects, config_vars, c_id = test_oracle(oracle, elements, config_objects, config_vars, c_id)
    test_quam(quam, elements, config_objects, config_vars, c_id)

    assert True

test_resonator_spectroscopy_separated()



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
