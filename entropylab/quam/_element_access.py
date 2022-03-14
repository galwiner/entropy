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
        self._element = element
        self._context: _UserElementContext = context

    def __getattr__(self, item):
        # TODO - add here a real wrapper for auto complete
        if hasattr(self._element, item):
            return _AdminElementAccess(getattr(self._element, item), self._context)
        else:
            raise AttributeError(f"attribute {item} is not found")

    def __setattr__(self, item, value):
        if hasattr(self._element, item):
            attr = getattr(self._element, item)
            if (
                    isinstance(attr, dict)
                    and "type_cls" in attr
                    and attr["type_cls"] == "UserParameter"
            ):
                param: Parameter = self._context.get_user_parameter(name=attr["name"])
                param.set_value(value)
            else:
                raise AttributeError(f"quam user can not set attribute {item} value")
        else:
            object.__setattr__(self, item, value)


class _UserElementAccess(Munch):
    is_frozen = False

    def __init__(self, element: Munch, context: _UserElementContext) -> None:
        super().__init__()
        self._element = element
        self._context: _UserElementContext = context
        self.is_frozen = True

    def __getattr__(self, item):
        # TODO - add here a real wrapper for auto complete
        if self.is_frozen and hasattr(self._element, item):
            return _UserElementAccess(getattr(self._element, item), self._context)
        else:
            try:
                object.__getattribute__(self, item)
            except BaseException:
                raise AttributeError(f"attribute {item} is not found")

    def __setattr__(self, item, value):
        if self.is_frozen and item in self._element:
            attr = self._element[item]
            if (
                    isinstance(attr, dict)
                    and "type_cls" in attr
                    and attr["type_cls"] == "UserParameter"
            ):
                param: Parameter = self._context.core.get_user_parameter(
                    name=attr["name"]
                )
                param.set_value(value)
            else:
                raise AttributeError(f"quam user can not set attribute {item} value")
        else:
            object.__setattr__(self, item, value)
