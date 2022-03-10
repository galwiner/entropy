import enum

from qm.QuantumMachinesManager import QuantumMachinesManager

from entropylab.quam.admin import QuamAdmin
from entropylab.quam.tests.dummy_driver import DummyDC


def test_can_update_instrument(tmpdir):
    admin = QuamAdmin(tmpdir)
    admin.add_instrument(
        name="flux_driver", resource_class=DummyDC, args=["flux_driver"]
    )

    admin.update_instrument(
        name="flux_driver", resource_class=DummyDC, args=["flux_driver"]
    )
    raise NotImplementedError()


def test_qop_different_settings(tmpdir):
    class QOPINFO(enum.Enum):
        auto = enum.auto()
        user = enum.auto()

    admin = QuamAdmin(tmpdir)
    admin.set_qop(host="127.0.0.1", port=80)
    admin.set_qop(QuantumMachinesManager())
    admin.set_qop(QOPINFO.auto)
    admin.set_qop(QOPINFO.user)
