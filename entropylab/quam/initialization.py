from entropylab.quam.admin import QuamAdmin
from entropylab.quam.oracle import QuamOracle
from entropylab.quam.user import QuamUser


def quam_init(path="."):
    # this function initializes the quam system (it will be part of the quam)

    quam = QuamUser(path)
    admin = QuamAdmin(path)
    oracle = QuamOracle(path)

    return admin, quam, oracle
