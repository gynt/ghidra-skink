from dataclasses import dataclass, field

from dataclasses_json import dataclass_json

from generator.architecture.export.style import AbstractStyle, NamespaceStyle

@dataclass_json
@dataclass
class AbstractContext(object):

    def copy[Context](self) -> Context:
        return self.from_json(self.to_json())

    def mutate[Context](self, k, v) -> Context:
        ctx = self.copy()
        if not hasattr(ctx, k):
            raise Exception(f"Style {ctx} does not have attribue {k}")
        setattr(ctx, k, v)
        return ctx


@dataclass_json
@dataclass
class IncludeRules(AbstractContext):
    functions_this_parameter_type: bool


@dataclass_json
@dataclass
class ClassRules(AbstractContext):
    prefix: str


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
    include: IncludeRules = field(default_factory=lambda: IncludeRules(False))
    function_rules: FunctionRules = field(default_factory=lambda: FunctionRules())
    class_rules: ClassRules = field(default_factory=lambda: ClassRules(""))


DEFAULT = Context()