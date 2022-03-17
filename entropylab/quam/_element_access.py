from munch import Munch

from entropylab.quam.core import _QuamCore
from entropylab.quam.instruments_wrappers import FunctionInfo
from entropylab.quam.quam_components import Parameter


class _UserElementContext:
    def __init__(self, core: _QuamCore) -> None:
        super().__init__()
        self.core = core


class _AdminElementAccess(Munch):
    def __init__(self, element: dict, context: _UserElementContext) -> None:
        super().__init__()
        for e in element.keys():
            super(_AdminElementAccess, self).__setattr__(e, element[e])
        super(_AdminElementAccess, self).__setattr__("_context", context)

    def __getitem__(self, item):
        res = super(_AdminElementAccess, self).__getitem__(item)
        if isinstance(res, dict):
            if "type_cls" in res:
                if res["type_cls"] == "UserParameter":
                    return super(_AdminElementAccess, self).__getattr__("_context").core.get_user_parameter(name=res["name"])
                elif res["type_cls"] == "FunctionInfo":
                    # TODO make dict no serializer
                    return FunctionInfo(
                        instrument_name=res["instrument_name"],
                        function_name=res["function_name"],
                        resource=res["resource"]
                    )
                else:
                    # TODO type not supported?
                    return _AdminElementAccess(res, super(_AdminElementAccess, self).__getattr__("_context"))
            else:
                return _AdminElementAccess(res, super(_AdminElementAccess, self).__getattr__("_context"))
        else:
            return res

    def __setattr__(self, item, value):
        super(_AdminElementAccess, self).__setattr__(item, value)


class _UserElementAccess(Munch):
    def __init__(self, element: dict, context: _UserElementContext) -> None:
        super().__init__()
        # TODO it's not the actual munch?
        for e in element.keys():
            super(_UserElementAccess, self).__setattr__(e, element[e])
        super(_UserElementAccess, self).__setattr__("_context", context)

    def __getitem__(self, item):
        res = super(_UserElementAccess, self).__getitem__(item)
        if isinstance(res, dict):
            if "type_cls" in res:
                if res["type_cls"] == "UserParameter":
                    return super(_UserElementAccess, self).__getattr__("_context").core.get_user_parameter(name=res["name"])
                elif res["type_cls"] == "FunctionInfo":
                    # TODO make dict no serializer
                    return FunctionInfo(
                        instrument_name=res["instrument_name"],
                        function_name=res["function_name"],
                        resource=res["resource"]
                    )
                else:
                    # TODO type not supported?
                    return _UserElementAccess(res, super(_UserElementAccess, self).__getattr__("_context"))
            else:
                return _UserElementAccess(res, super(_UserElementAccess, self).__getattr__("_context"))
        else:
            return res

    def __setattr__(self, item, value):
        res = super(_UserElementAccess, self).__getitem__(item)
        # TODO this is user?
        if (
                isinstance(res, dict)
                and "type_cls" in res
                and res["type_cls"] == "UserParameter"
        ):
            param: Parameter = super(_UserElementAccess, self).__getattr__("_context").core.get_user_parameter(name=res["name"])
            param.set_value(value)
        else:
            raise AttributeError(f"quam user can not set attribute {item} value")
