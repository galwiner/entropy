from munch import Munch

from entropylab.quam.core import _QuamCore
from entropylab.quam.quam_components import Parameter


class _UserElementContext:
    def __init__(self, core: _QuamCore) -> None:
        super().__init__()
        self.core = core


class _AdminElementAccess(Munch):
    def __init__(self, element: dict, context: _UserElementContext) -> None:
        super().__init__()
        # TODO it's not the actual munch?
        for e in element.keys():
            super(_AdminElementAccess, self).__setattr__(e, element[e])
        super(_AdminElementAccess, self).__setattr__("_context", context)

    def __getattr__(self, item):
        res = super(_AdminElementAccess, self).__getattr__(item)
        if isinstance(res, dict):
            return _AdminElementAccess(res, super(_AdminElementAccess, self).__getattr__("_context"))
        else:
            return res
        # TODO - add here a real wrapper for auto complete?

    def __setattr__(self, item, value):
        res = super(_AdminElementAccess, self).__getattr__(item)
        # TODO this is user?
        if (
                isinstance(res, dict)
                and "type_cls" in res
                and res["type_cls"] == "UserParameter"
        ):
            param: Parameter = super(_AdminElementAccess, self).__getattr__("_context").get_user_parameter(name=res["name"])
            param.set_value(value)
        else:
            raise AttributeError(f"quam user can not set attribute {item} value")


class _UserElementAccess(Munch):
    def __init__(self, element: dict, context: _UserElementContext) -> None:
        super().__init__()
        # TODO it's not the actual munch?
        for e in element.keys():
            super(_UserElementAccess, self).__setattr__(e, element[e])
        super(_UserElementAccess, self).__setattr__("_context", context)

    def __getattr__(self, item):
        res = super(_UserElementAccess, self).__getattr__(item)
        if isinstance(res, dict):
            return _UserElementAccess(res, super(_UserElementAccess, self).__getattr__("_context"))
        else:
            return res
        # TODO - add here a real wrapper for auto complete?

    def __setattr__(self, item, value):
        res = super(_UserElementAccess, self).__getattr__(item)
        # TODO this is user?
        if (
                isinstance(res, dict)
                and "type_cls" in res
                and res["type_cls"] == "UserParameter"
        ):
            param: Parameter = super(_UserElementAccess, self).__getattr__("_context").get_user_parameter(name=res["name"])
            param.set_value(value)
        else:
            raise AttributeError(f"quam user can not set attribute {item} value")
