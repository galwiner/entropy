import dataclasses

from munch import Munch

from entropylab import LabResources


@dataclasses.dataclass
class FunctionInfo:
    instrument_name: str
    function_name: str


class FunctionRef:
    _is_frozen = False

    def __init__(self, instrument_name: str, function_name: str, resource) -> None:
        super().__init__()

        self._instrument_name: str = instrument_name
        self._function_name: str = function_name
        # self._resource = resource
        self._resource = None
        self._is_frozen = True

    def __getattr__(self, k):
        if self._is_frozen:
            # TODO check the function exists on the resource? if not, remove the resource from this class
            return FunctionRef(
                self._instrument_name, f"{self._function_name}.{k}", self._resource
            )


class InstrumentFunctionWrapper:
    _is_frozen = False

    def __init__(self, name, resource) -> None:
        super().__init__()
        self._name = name
        self._resource = resource
        self._is_frozen = True

    def __getattr__(self, k):
        if self._is_frozen:
            return FunctionRef(self._name, k, self._resource)

    def __setattr__(self, k, v):
        if self._is_frozen:
            raise Exception("can not set attribute of instrument wrapper")
        else:
            super(InstrumentFunctionWrapper, self).__setattr__(k, v)

    def __delattr__(self, k):
        if self._is_frozen:
            raise Exception("can not delete attribute of instrument wrapper")
        else:
            super(InstrumentFunctionWrapper, self).__delattr__(k)


class InstrumentAccess(Munch):
    def __init__(self, resources) -> None:
        super().__init__()
        self._resources: LabResources = resources

    def __getattr__(self, item):
        # TODO - add here a real wrapper for auto complete
        resources = super().__getattr__("_resources")
        if resources.resource_exist(item):
            return InstrumentFunctionWrapper(item, resources.get_resource(item))
        else:
            raise KeyError(f"Resource {item} is not found")
