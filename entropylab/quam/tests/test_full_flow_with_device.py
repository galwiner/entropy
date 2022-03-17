import numpy as np
import qualang_tools.config.components as cb
from qm import SimulationConfig
from qm.qua import *
from qualang_tools.config.primitive_components import Operation, Weights, Matrix2x2

from entropylab.quam.admin import QuamAdmin
from entropylab.quam.initialization import quam_init
from entropylab.quam.quam_components import QuamElement
from entropylab.quam.tests.dummy_driver import DummyDC
from entropylab.quam.user import QuamUser


class QuamFluxTunableXmon(cb.Transmon, QuamElement):
    def __init__(self, flux_channel, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_quam_attribute("flux_channel", flux_channel)


def admin_part(admin: QuamAdmin):
    admin.set_qop(host="127.0.0.1", port=80)
    cont = admin.add_controller(name="cont1", type="opx+")
    admin.add_instrument(
        name="flux_driver", resource_class=DummyDC, args=["flux_driver"]
    )

    xmon = QuamFluxTunableXmon(
        name="xmon",
        I=cont.analog_output(1),
        Q=cont.analog_output(2),
        intermediate_frequency=admin.parameter("xmon_if"),
        flux_channel=admin.parameter(
            "flux_driver", setter=admin.instruments.flux_driver.v1
        ),
    )

    xmon.lo_frequency = admin.parameter("xmon_lo")

    xmon.mixer = cb.Mixer(
        name="xmon_mixer",
        intermediate_frequency=admin.parameter("xmon_if"),
        lo_frequency=admin.parameter("xmon_lo"),
        correction=Matrix2x2([[1, 0], [0, 1]]),
    )

    xmon.add_quam_attribute("more info", "the right one")

    admin.add(xmon)

    ror = cb.ReadoutResonator(
        name="ror",
        outputs=[cont.analog_output(4), cont.analog_output(5)],
        inputs=[cont.analog_input(1), cont.analog_input(2)],
        intermediate_frequency=admin.parameter("ror_if"),
    )
    ror.lo_frequency = admin.parameter("ror_lo")
    ror.mixer = cb.Mixer(
        name="ror_mixer",
        intermediate_frequency=admin.parameter("ror_if"),
        lo_frequency=admin.parameter("ror_lo"),
        correction=Matrix2x2([[1, 0], [0, 1]]),  # TODO: add default correction matrix
    )
    ro_pulse = cb.MeasurePulse(
        "readout_pulse",
        [
            cb.ConstantWaveform("readout_wf", admin.parameter("ro_amp")),
            cb.ConstantWaveform("wf_zero", 0),
        ],
        admin.parameter("ro_duration"),
    )
    ro_pulse.add(
        Weights(
            cb.ConstantIntegrationWeights(
                "w1",
                cosine=1,
                sine=0,
                duration=admin.parameter("ro_duration"),
            )
        )
    )
    ro_pulse.add(
        Weights(
            cb.ConstantIntegrationWeights(
                "w2",
                cosine=0,
                sine=1,
                duration=admin.parameter("ro_duration"),
            )
        )
    )
    ror.add(Operation(ro_pulse))
    ror.time_of_flight = 24

    admin.add(ror)

    #TODO gal - should this work? if it's a user parameter, it will disable it form being a user parameter?
    admin.elements.ror.time_of_flight = 28

    admin.user_parameters.list_names()
    admin.user_parameters.xmon_if = 10e6
    admin.user_parameters["xmon_if"] = 10e6
    admin.user_parameters["xmon_lo"] = 10e6
    admin.user_parameters["pi_wf_samples"] = list(
        np.random.rand(1000)
    )  # TODO check if param store supports it
    admin.user_parameters["ror_if"] = 1e6
    admin.user_parameters["ror_lo"] = 1e6
    admin.user_parameters["ro_amp"] = 1e-2
    admin.user_parameters["ro_duration"] = 200e-9

    commit_id = admin.commit("set config vars")

    print(admin.user_parameters.ro_amp)
    assert admin.user_parameters.ro_amp == 1e-2
    admin.checkout(commit_id)  # checking we can also checkout from the ParamStore

    print(admin.elements.ror.time_of_flight)

    admin.set_default_commit(commit_id)

    return commit_id  # this is a temporary solution for communicating between the three interfaces


def oracle_part(oracle, commit_id):
    assert set(oracle.element_names) == {
        "cont1",
        "xmon",
        "ror",
    }  # element can be non qua elements. maybe we need to rename. maybe this should be seperate from qua
    assert set(oracle.qua_element_names) == {"cont1", "ror", "xmon"}
    commit_list = oracle.database.list_commits("set config vars")
    oracle.database.checkout(
        commit_id
    )  # make sure checkout from the oracle is possible.
    assert oracle.operations("ror") == ["readout_pulse"]
    assert oracle.integration_weights == ["w1", "w2"]
    assert set(oracle.user_params) == {
        "pi_wf_samples",
        "ro_amp",
        "ro_duration",
        "xmon_if",
        "xmon_lo",
        "ror_if",
        "ror_lo",
    }
    return commit_id


def quam_user_part(quam: QuamUser, commit_id):
    quam.utils.checkout(commit_id)
    before = quam.utils.config

    # user sets some parameters
    quam.utils.get_user_parameters()
    quam.xmon.lo_frequency = 2e9
    quam.xmon.flux_channel = 500
    # TODO allow this as well:
    # quam.xmon.flux_channel(12, g=7)

    after = quam.utils.config
    assert not before == after

    quam.utils.commit("flux sweep")

    # now start the experiment
    # TODO:
    # quam.elements.xmon.flux_channel(sweep=(start,stop,duration))#sets up an instrument

    f_start = 10
    f_end = 20
    df = 5

    with program() as prog:
        f = declare(int)
        I = declare(fixed)
        Q = declare(fixed)
        I_str = declare_stream()
        Q_str = declare_stream()
        with for_(f, f_start, f < f_end, f + df):
            # quam.qua_executor.wait_for_external(
            #     quam.xmon.set_flux,
            #     (x for x in range(f_start, f_end, df)),
            #     interval_wait=0.1,
            # )
            update_frequency(quam.ror, f)
            measure(
                quam.ror.pulses.readout_pulse,
                quam.ror,
                None,
                demod.full(quam.ror.integration_weights.w1, I, "out1"),
                demod.full(quam.ror.integration_weights.w2, Q, "out2"),
                # TODO maybe add function that gets all iw from all elements - than it's all should be different
            )
            save(I, I_str)
            save(Q, Q_str)
        with stream_processing():
            I_str.save_all("I_out")
            Q_str.save_all("Q_out")

    # quam.qua_executor.run(prog)
    # quam.utils.execute_qua(prog)
    res = quam.utils.execute_qua(
        prog, simulation_config=SimulationConfig(duration=10000), use_simulator=True
    )
    assert hasattr(res.result_handles, "I_out")
    assert hasattr(res.result_handles, "Q_out")


def test_flux_tunable_qubit(tmpdir):
    admin, quam, oracle = quam_init(tmpdir)
    commit_id = admin_part(admin)
    commit_id = oracle_part(oracle, commit_id)
    quam_user_part(quam, commit_id)

    assert True
