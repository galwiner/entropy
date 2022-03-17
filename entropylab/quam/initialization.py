from entropylab.quam.admin import QuamAdmin
from entropylab.quam.core import _QuamCore
from entropylab.quam.oracle import QuamOracle
from entropylab.quam.user import QuamUser


def quam_init(path="."):
    # this function initializes the quam system (it will be part of the quam)

    core = _QuamCore(path)
    quam = QuamUser(core)
    admin = QuamAdmin(core)
    oracle = QuamOracle(core)

    return admin, quam, oracle
