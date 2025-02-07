from dataclasses import dataclass, field
from typing import TypeVar

from dataclasses_json import dataclass_json

from skink.architecture.export.style import AbstractStyle, NamespaceStyle

C = TypeVar('C', bound="AbstractContext")

@dataclass_json
@dataclass
class AbstractContext(object):

    def copy(self) -> "AbstractContext":
        return self.from_json(self.to_json())

    def mutate(self, **kwargs) -> "AbstractContext":
        return type(self)(**kwargs)


@dataclass_json
@dataclass
class IncludeRules(AbstractContext):
    functions_this_parameter_type: bool


@dataclass_json
@dataclass
class ClassRules(AbstractContext):
    prefix: str = ""


@dataclass_json
@dataclass
class FunctionRules(AbstractContext):
    virtual: bool = False
    include_convention: bool = True
    include_this: bool = True


@dataclass_json
@dataclass
class Context(AbstractContext):
    root: str = ""
    style: AbstractStyle = field(default_factory=lambda: NamespaceStyle)
    promote_to_class: bool = True
    include: IncludeRules = field(default_factory=lambda: IncludeRules())
    function_rules: FunctionRules = field(default_factory=lambda: FunctionRules())
    class_rules: ClassRules = field(default_factory=lambda: ClassRules())


DEFAULT = Context()