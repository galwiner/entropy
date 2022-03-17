import abc
from typing import List, Union, Tuple, Optional, Dict, Any

import qualang_tools.config.components as config_components
import qualang_tools.config.primitive_components as config_p_components
from qualang_tools.config.parameters import _is_callable

from entropylab.quam.instruments_wrappers import FunctionInfo


class QuamElement(abc.ABC):
    def __init__(self) -> None:
        super().__init__()
        self.quam_attributes: Dict = {}

    def add_quam_attribute(self, name, value):
        self.quam_attributes[name] = value


class Parameter:
    def __init__(self, d: Dict):
        super(Parameter, self).__init__()
        self.d = d

    @property
    def name(self):
        return self.d["name"]

    def __call__(self, *args, **kwargs):
        if self.d["setter"] is not None:
            return self.d["setter"](*args, **kwargs)
        elif self.d["is_value_set"]:
            return self.d["value"]
        else:
            raise AssertionError(f"Parameter {self.name} is not set")

    @property
    def value(self):
        return self.d["value"]

    @value.setter
    def value(self, v):
        return self.set_value(v)

    def set_value(self, value, *args, **kwargs):
        self.d["is_value_set"] = True
        self.d["value"] = value
        if "setter" in self.d and self.d["setter"] is not None:
            return self.d["setter"](*args, **kwargs)


class _QuamParameters(object):
    def __init__(self, parameters: Optional[Dict] = None):
        if parameters is None:
            parameters = {}
        self.parameters_dicts = parameters

    @staticmethod
    def _sanitize_name(name):
        if name.find(" ") != -1:
            raise ValueError(
                "Parameter name cannot contain spaces. " "Use underscore of camelCase."
            )

    def parameter(self, name, setter=None, **kwargs):
        self._sanitize_name(name)
        if name not in self.parameters_dicts.keys():
            self.parameters_dicts[name] = {
                "name": name,
                "value": None
            }
            if "initial" in kwargs:
                initial = kwargs.get("initial")
                self.parameters_dicts[name]["initial"] = initial
                self.parameters_dicts[name]["value"] = initial
            if setter is not None:
                if isinstance(setter, FunctionInfo):
                    self.parameters_dicts[name]["setter"] = setter
                    self.parameters_dicts[name]["is_set"] = True
                elif _is_callable(setter):
                    # todo get source code:
                    raise NotImplementedError()
                else:
                    raise ValueError("setter format is not supported")

        # TODO check that no setter if it's already exist?
        return self.get_config_var(name)

    def set(self, **kwargs):
        for name, value in kwargs.items():
            if name not in self.parameters_dicts.keys():
                self.parameters_dicts[name] = {}
            self.parameters_dicts[name]["value"] = value
            self.parameters_dicts[name]["is_set"] = True

    def get_names(self):
        return self.parameters_dicts.keys()

    def get_config_var(self, name):
        return Parameter(self.parameters_dicts[name])


class _QuamElements(object):
    def __init__(self, elements: Optional[Dict] = None):
        if elements is None:
            elements = {}
        self._elements_dicts = elements

    def get_names(self):
        return list(self._elements_dicts.keys())

    def get_elements(self):
        return self._elements_dicts.values()

    def get(self, item):
        return self._elements_dicts[item]


def _config_builder_to_dict(obj, name):
    d = {
        "name": name,
        "type_cls": obj.__class__.__name__,
    }

    if (
        isinstance(obj, config_p_components.AnalogOutputPort)
        or isinstance(obj, config_p_components.DigitalOutputPort)
        or isinstance(obj, config_p_components.DigitalInputPort)
        or isinstance(obj, config_p_components.AnalogOutputFilter)
        or isinstance(obj, config_p_components.AnalogInputPort)
    ):
        d.update(obj.__dict__)
    elif isinstance(obj, config_components.MeasurePulse):
        d["wfs"] = [_config_builder_to_dict(wf, wf.name) for wf in obj.wfs]
        d["length"] = obj.length
        d["integration_weights"] = [
            _config_builder_to_dict(iw, iw.name) for iw in obj.integration_weights
        ]
        d["digital_marker"] = obj.digital_marker
    elif isinstance(obj, config_components.ControlPulse):
        d["wfs"] = [_config_builder_to_dict(wf, wf.name) for wf in obj.wfs]
        d["length"] = obj.length
        d["digital_marker"] = obj.digital_marker
    elif isinstance(obj, config_p_components.Pulse):
        d["wfs"] = [_config_builder_to_dict(wf, wf.name) for wf in obj.wfs]
        d["operation"] = obj.operation
        d["length"] = obj.length
        d["digital_marker"] = obj.digital_marker
    elif isinstance(obj, config_p_components.Operation):
        p = _config_builder_to_dict(obj.pulse, obj.pulse.name)
        d["pulse"] = p
    elif isinstance(obj, config_p_components.Weights):
        d["weights"] = _config_builder_to_dict(obj.weights, obj.weights.name)
    elif isinstance(obj, config_components.Controller):
        d["controller_type"] = obj.controller_type
        d["analog_outputs"] = [
            _config_builder_to_dict(p, p.info) for p in obj.analog_output_ports
        ]
        d["analog_inputs"] = [
            _config_builder_to_dict(p, p.info) for p in obj.analog_input_ports
        ]
        d["digital_outputs"] = [
            _config_builder_to_dict(p, p.info) for p in obj.digital_output_ports
        ]
        d["digital_inputs"] = [
            _config_builder_to_dict(p, p.info) for p in obj.digital_input_ports
        ]
    elif isinstance(obj, config_components.ArbitraryWaveform):
        d["samples"] = obj.samples
    elif isinstance(obj, config_components.ConstantWaveform):
        d["sample"] = obj.sample
    elif isinstance(obj, config_components.DigitalWaveform):
        d["samples"] = [(ds.state, ds.duration) for ds in obj.samples]
    elif isinstance(obj, config_components.Mixer):
        d["intermediate_frequency"] = obj.intermediate_frequency
        d["lo_frequency"] = obj.lo_frequency
        d["correction"] = obj.correction.data
    elif isinstance(obj, config_components.MeasureElement):
        _set_element_in_dict(d, obj)
        d["time_of_flight"] = obj.time_of_flight
        d["smearing"] = obj.smearing
    elif isinstance(obj, config_components.Element):
        _set_element_in_dict(d, obj)
    elif isinstance(obj, config_components.ConstantIntegrationWeights):
        d["duration"] = obj._duration
        d["cosine"] = obj._cosine
        d["sine"] = obj._sine
    elif isinstance(obj, config_components.ArbitraryIntegrationWeights):
        d["cosine"] = obj.cosine
        d["sine"] = obj.sine
    elif isinstance(obj, config_p_components.IntegrationWeights):
        d["cosine"] = obj.cosine
        d["sine"] = obj.sine
    elif isinstance(obj, config_components.Oscillator):
        d["intermediate_frequency"] = obj.intermediate_frequency
        d["lo_frequency"] = obj.lo_frequency
        d["mixer"] = obj.mixer
    elif isinstance(obj, config_components.ReadoutResonator):
        d["intermediate_frequency"] = obj.intermediate_frequency
        d["output_ports"] = [
            _config_builder_to_dict(p, p.info) for p in obj.output_ports
        ]
        d["input_ports"] = [_config_builder_to_dict(p, p.info) for p in obj.input_ports]
        d["operations"] = [
            _config_builder_to_dict(op, op.name) for op in obj.drive_operations
        ]
        d["time_of_flight"] = obj.time_of_flight
        d["smearing"] = obj.smearing
        d["mixer"] = _config_builder_to_dict(obj.mixer, obj.mixer.name)
        # d["correction"] = obj.mixer.correction
        d["lo_frequency"] = obj.lo_frequency
    elif isinstance(obj, config_components.FluxTunableTransmon):
        d["intermediate_frequency"] = obj.intermediate_frequency
        d["operations"] = [
            _config_builder_to_dict(op, op.name) for op in obj.drive_operations
        ]
        d["flux_operations"] = [
            _config_builder_to_dict(op, op.name) for op in obj.flux_operations
        ]
        d["I"] = _config_builder_to_dict(obj.drive_I, obj.drive_I.info)
        d["Q"] = _config_builder_to_dict(obj.drive_Q, obj.drive_Q.info)
        d["flux_port"] = _config_builder_to_dict(obj.flux_port, obj.flux_port.info)
        d["mixer"] = _config_builder_to_dict(obj.mixer, obj.mixer.name)
        d["lo_frequency"] = obj.lo_frequency
    elif isinstance(obj, config_components.Transmon):
        d["intermediate_frequency"] = obj.intermediate_frequency
        if hasattr(obj, "drive_operations") and obj.drive_operations is not None:
            d["operations"] = [
                _config_builder_to_dict(op, op.name) for op in obj.drive_operations
            ]
        d["I"] = _config_builder_to_dict(obj.drive_I, obj.drive_I.info)
        d["Q"] = _config_builder_to_dict(obj.drive_Q, obj.drive_Q.info)
        if hasattr(obj, "mixer") and obj.mixer is not None:
            d["mixer"] = _config_builder_to_dict(obj.mixer, obj.mixer.name)
        if hasattr(obj, "lo_frequency") and obj.lo_frequency is not None:
            d["lo_frequency"] = obj.lo_frequency
    elif isinstance(obj, config_components.Coupler):
        d["operations"] = [
            _config_builder_to_dict(op, op.name) for op in obj.operations
        ]
        d["port"] = _config_builder_to_dict(obj.port, obj.port.info)
    else:
        # TODO!
        raise NotImplementedError()

    return d


def _set_element_in_dict(d, obj):
    d["intermediate_frequency"] = obj.intermediate_frequency
    d["pulses"] = [_config_builder_to_dict(p, p.name) for p in obj.pulses]
    d["operations"] = obj.operations
    if obj.has_lo_frequency:
        d["lo_frequency"] = obj.lo_frequency
    if obj.has_signal_threshold:
        d["signal_threshold"] = obj.signal_threshold
    if obj.has_signal_polarity:
        d["signal_polarity"] = obj.signal_polarity
    if obj.has_derivative_threshold:
        d["derivative_threshold"] = obj.derivative_threshold
    if obj.has_derivative_polarity:
        d["derivative_polarity"] = obj.derivative_polarity
    d["analog_outputs"] = [
        _config_builder_to_dict(p, p.info) for p in obj.analog_output_ports
    ]
    d["analog_inputs"] = [
        _config_builder_to_dict(p, p.info) for p in obj.analog_input_ports
    ]
    d["digital_outputs"] = [
        _config_builder_to_dict(p, p.info) for p in obj.digital_output_ports
    ]
    d["digital_inputs"] = [
        _config_builder_to_dict(p, p.info) for p in obj.digital_input_ports
    ]


def _kwargs_from_dict(d: Dict, names: List[Union[str, Tuple[str]]], parameters):
    # names are either names both in the keyword and in the dict, or mapping keyword->dict
    kw = {}
    for name in names:
        if isinstance(name, str):
            if name in d:
                kw[name] = _dict_to_config_builder(d[name], parameters)
        else:
            if name[1] in d:
                kw[name[0]] = _dict_to_config_builder(d[name[1]], parameters)

    return kw


def _element_kwargs_from_dict(d, parameters) -> Dict:
    kw = {}
    if "analog_inputs" in d:
        kw["analog_input_ports"] = [
            _dict_to_config_builder(p, parameters) for p in d["analog_inputs"]
        ]
    if "analog_outputs" in d:
        kw["analog_output_ports"] = [
            _dict_to_config_builder(p, parameters) for p in d["analog_outputs"]
        ]
    if "digital_inputs" in d:
        kw["digital_input_ports"] = [
            _dict_to_config_builder(p, parameters) for p in d["digital_inputs"]
        ]
    if "digital_outputs" in d:
        kw["digital_output_ports"] = [
            _dict_to_config_builder(p, parameters) for p in d["digital_outputs"]
        ]
    if "mixer" in d:
        kw["mixer"] = _dict_to_config_builder(d["mixer"], parameters)
    if "pulses" in d:
        kw["pulses"] = [_dict_to_config_builder(p, parameters) for p in d["pulses"]]
    kw.update(
        _kwargs_from_dict(
            d,
            [
                "name",
                "intermediate_frequency",
                "lo_frequency",
                "operations",
                "signal_threshold",
                "signal_polarity",
                "derivative_threshold",
                "derivative_polarity",
            ],
            parameters,
        )
    )
    return kw


def _dict_to_config_builder(d: Dict, parameters: _QuamParameters) -> Any:
    if not d or not isinstance(d, dict) or "type_cls" not in d:
        return d

    if d["type_cls"] == "UserParameter":
        return parameters.get_config_var(d["name"])
    elif d["type_cls"] == "Controller":
        return config_components.Controller(
            name=d["name"],
            analog_outputs=[
                _dict_to_config_builder(p, parameters) for p in d["analog_outputs"]
            ],
            # TODO filter None?
            analog_inputs=[
                _dict_to_config_builder(p, parameters) for p in d["analog_inputs"]
            ],
            digital_outputs=[
                _dict_to_config_builder(p, parameters) for p in d["digital_outputs"]
            ],
            digital_inputs=[
                _dict_to_config_builder(p, parameters) for p in d["digital_inputs"]
            ],
            controller_type=d["controller_type"],
        )
    elif d["type_cls"] == "AnalogInputPort":
        return config_p_components.AnalogInputPort(
            **_kwargs_from_dict(
                d, ["controller", "port_id", "offset", "gain_db"], parameters
            )
        )
    elif d["type_cls"] == "AnalogOutputPort":
        return config_p_components.AnalogOutputPort(
            **_kwargs_from_dict(
                d,
                [
                    "controller",
                    "port_id",
                    "offset",
                    "delay",
                    "filter",
                    "channel_weights",
                ],
                parameters,
            )
        )
    elif d["type_cls"] == "DigitalInputPort":
        return config_p_components.DigitalInputPort(
            **_kwargs_from_dict(
                d,
                [
                    "controller",
                    "port_id",
                    "offset",
                    "polarity",
                    "window",
                    "threshold",
                ],
                parameters,
            )
        )
    elif d["type_cls"] == "DigitalOutputPort":
        return config_p_components.DigitalOutputPort(
            **_kwargs_from_dict(d, ["controller", "port_id", "offset"], parameters)
        )
    elif d["type_cls"] == "Pulse":
        wfs = [_dict_to_config_builder(wf, parameters) for wf in d["wfs"]]
        return config_p_components.Pulse(
            **_kwargs_from_dict(
                d, ["name", "operation", "length", "digital_marker"], parameters
            ),
            wfs=wfs,
        )
    elif d["type_cls"] == "MeasurePulse":
        wfs = [_dict_to_config_builder(wf, parameters) for wf in d["wfs"]]
        return config_components.MeasurePulse(d["name"], wfs, d["length"])
    elif d["type_cls"] == "ControlPulse":
        wfs = [_dict_to_config_builder(wf, parameters) for wf in d["wfs"]]
        return config_components.ControlPulse(d["name"], wfs, d["length"])
    elif d["type_cls"] == "Operation":
        p = _dict_to_config_builder(d["pulse"], parameters)
        return config_p_components.Operation(p, d["name"])
    elif d["type_cls"] == "IntegrationWeights":
        return config_p_components.IntegrationWeights(d["name"], d["cosine"], d["sine"])
    elif d["type_cls"] == "Weights":
        return config_p_components.Weights(
            _dict_to_config_builder(d["weights"], parameters),
            **_kwargs_from_dict(d, ["name"], parameters),
        )
    elif d["type_cls"] == "AnalogOutputFilter":
        return config_p_components.AnalogOutputFilter(d["feedback"], d["feedforward"])
    elif d["type_cls"] == "ArbitraryWaveform":
        return config_components.ArbitraryWaveform(d["name"], d["samples"])
    elif d["type_cls"] == "ConstantWaveform":
        return config_components.ConstantWaveform(d["name"], d["sample"])
    elif d["type_cls"] == "DigitalWaveform":
        return config_components.DigitalWaveform(
            d["name"],
            [config_components.DigitalSample(s[0], s[1]) for s in d["samples"]],
        )
    elif d["type_cls"] == "Mixer":
        return config_components.Mixer(
            d["name"],
            d["intermediate_frequency"],
            d["lo_frequency"],
            config_p_components.Matrix2x2(d["correction"]),
        )
    elif d["type_cls"] == "ConstantIntegrationWeights":
        return config_components.ConstantIntegrationWeights(
            d["name"],
            d["cosine"],
            d["sine"],
            d["duration"],
        )
    elif d["type_cls"] == "ArbitraryIntegrationWeights":
        return config_components.ArbitraryIntegrationWeights(
            d["name"],
            d["cosine"],
            d["sine"],
        )
    elif d["type_cls"] == "Element":
        return config_components.Element(**_element_kwargs_from_dict(d, parameters))
    elif d["type_cls"] == "MeasureElement":
        return config_components.MeasureElement(
            **_element_kwargs_from_dict(d, parameters),
            time_of_flight=d["time_of_flight"],
            smearing=d["smearing"],
        )
    elif d["type_cls"] == "ReadoutResonator":
        return config_components.ReadoutResonator(
            **_kwargs_from_dict(
                d,
                [
                    "name",
                    "intermediate_frequency",
                    "time_of_flight",
                    "smearing",
                    "lo_frequency",
                ],
                parameters,
            ),
            outputs=[
                _dict_to_config_builder(op, parameters) for op in d["output_ports"]
            ],
            inputs=[_dict_to_config_builder(op, parameters) for op in d["input_ports"]],
            mixer=_dict_to_config_builder(d["mixer"], parameters),
            operations=[
                _dict_to_config_builder(op, parameters) for op in d["operations"]
            ],
        )
    elif d["type_cls"] == "Transmon":
        return config_components.Transmon(
            **_kwargs_from_dict(
                d,
                [
                    "name",
                    "intermediate_frequency",
                    "lo_frequency",
                ],
                parameters,
            ),
            mixer=_dict_to_config_builder(d["mixer"], parameters),
            I=_dict_to_config_builder(d["I"], parameters),
            Q=_dict_to_config_builder(d["Q"], parameters),
            operations=[
                _dict_to_config_builder(op, parameters) for op in d["operations"]
            ],
        )
    elif d["type_cls"] == "FluxTunableTransmon":
        return config_components.FluxTunableTransmon(
            **_kwargs_from_dict(
                d,
                [
                    "name",
                    "intermediate_frequency",
                    "lo_frequency",
                ],
                parameters,
            ),
            mixer=_dict_to_config_builder(d["mixer"], parameters),
            I=_dict_to_config_builder(d["I"], parameters),
            Q=_dict_to_config_builder(d["Q"], parameters),
            flux_port=_dict_to_config_builder(d["flux_port"], parameters),
            operations=[
                _dict_to_config_builder(op, parameters) for op in d["operations"]
            ],
            flux_operations=[
                _dict_to_config_builder(op, parameters) for op in d["flux_operations"]
            ],
        )
    elif d["type_cls"] == "Coupler":
        return config_components.Coupler(
            name=d["name"],
            port=_dict_to_config_builder(d["port"], parameters),
            operations=[
                _dict_to_config_builder(op, parameters) for op in d["operations"]
            ],
        )
    elif d["type_cls"] == "Oscillator":
        return config_components.Oscillator(
            d["name"],
            d["intermediate_frequency"],
            d["lo_frequency"],
            d["mixer"],
        )
    else:
        # TODO!
        raise NotImplementedError()
