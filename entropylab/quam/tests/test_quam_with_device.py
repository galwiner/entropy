from entropylab.quam.initialization import quam_init


def test_flux_tunable_qubit_when_db_is_not_empty():
    # TODO
    raise NotImplementedError()


def test_user_defined_config_builder_extension():
    # TODO
    # Should create a mapping model from quam -> config builder
    raise NotImplementedError()


def test_quam_with_device_driver_function(tmpdir):
    raise NotImplementedError()


def test_quam_with_device_custom_setter(tmpdir):
    admin, quam, oracle = quam_init(tmpdir)

    def flux_setter(quam_user, value):
        quam_user.instruments.flux_driver.v1 = value

    admin.elements.xmon.flux_channel = admin.parameter(
        "flux_driver", setter=flux_setter
    )
    raise NotImplementedError()


def test_quam_with_device_setter_getter(tmpdir):
    admin, quam, oracle = quam_init(tmpdir)

    admin.elements.xmon.flux_channel = admin.parameter(
        "flux_driver",
        setter=admin.instruments.flux_driver.v1,
        getter=admin.instruments.flux_driver.get_v1,
    )
    raise NotImplementedError()


def test_working_with_multiple_qms(tmpdir):
    # TODO define API
    # admin.add_quantum_machine(name="qm1", elements=["ror", admin.elements.xmon])
    # admin.add_quantum_machine(name="qm1", QM.ALL)
    # admin.add_quantum_machine(name="qm1", QM.USER)
    raise NotImplementedError()
