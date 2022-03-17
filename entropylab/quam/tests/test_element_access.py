from _pytest.fixtures import fixture

from entropylab.quam._element_access import _AdminElementAccess, _UserElementContext, _UserElementAccess
from entropylab.quam.admin import QuamAdmin
from entropylab.quam.core import _QuamCore
from entropylab.quam.tests.dummy_driver import DummyDC
from entropylab.quam.tests.test_full_flow_with_device import QuamFluxTunableXmon


@fixture
def create_element(tmpdir):
    admin = QuamAdmin(tmpdir)
    admin.set_qop(host="127.0.0.1", port=80)
    cont = admin.add_controller(name="cont1", type="opx+")
    admin.add_instrument(
        name="flux_driver", resource_class=DummyDC, args=["flux_driver"]
    )

    xmon = QuamFluxTunableXmon(
        name="xmon",
        I=cont.analog_output(1, offset=1.0),
        Q=cont.analog_output(2),
        intermediate_frequency=admin.parameter("xmon_if"),
        flux_channel=admin.parameter(
            "flux_driver", setter=admin.instruments.flux_driver.v1
        ),
    )
    admin.add(xmon)
    admin.commit("test")

    return tmpdir


def test_user_get_set_attr(create_element):
    # element_access.ro_amp
    core = _QuamCore(create_element)
    c=core.database.list_commits("test")
    core.checkout(c[0].id)
    ea = _UserElementAccess(core.elements.get("xmon"), _UserElementContext(core))

    assert ea.I is not None
    assert isinstance(ea, dict)

    #TODO guy ask Gal - what happens here?
    # ea.xmon = QuamFluxTunableXmon(
    #     name="xmon",
    #     I=cont.analog_output(1),
    #     Q=cont.analog_output(2),
    #     intermediate_frequency=admin.parameter("xmon_if"),
    #     flux_channel=admin.parameter(
    #         "flux_driver", setter=admin.instruments.flux_driver.v1
    #     ),
    # )

    assert ea.I.offset == 1.0


    #parameters:
    # ea.xmon.intermediate_frequency
    #instruments
    # ea.xmon.flux_channel


def test_admin_get_set_attr(create_element):
    # element_access.ro_amp
    core = _QuamCore(create_element)
    c = core.database.list_commits("test")
    core.checkout(c[0].id)
    ea = _AdminElementAccess(core.elements._elements_dicts, _UserElementContext(core))

    assert ea.xmon is not None
    assert isinstance(ea.xmon, dict)

    #TODO guy ask Gal - what happens here?
    # ea.xmon = QuamFluxTunableXmon(
    #     name="xmon",
    #     I=cont.analog_output(1),
    #     Q=cont.analog_output(2),
    #     intermediate_frequency=admin.parameter("xmon_if"),
    #     flux_channel=admin.parameter(
    #         "flux_driver", setter=admin.instruments.flux_driver.v1
    #     ),
    # )

    assert ea.xmon.I.offset == 1.0


    #parameters:
    # ea.xmon.intermediate_frequency
    #instruments
    # ea.xmon.flux_channel


def test_get_set_dict(create_element):
    # element_access["ro_amp"]
    raise NotImplementedError()
