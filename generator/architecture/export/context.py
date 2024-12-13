from dataclasses import dataclass, field

from dataclasses_json import dataclass_json

from generator.architecture.export.style import AbstractStyle, NamespaceStyle

@dataclass_json
@dataclass
class IncludeRules:
    functions_this_parameter_type: bool


@dataclass_json
@dataclass
class ClassRules:
    prefix: str

@dataclass_json
@dataclass
class Context:
    root: str
    style: AbstractStyle
    promote_to_class: bool
    include: IncludeRules
    class_rules: ClassRules = field(default_factory=lambda: ClassRules(""))
    functions_virtual: bool = False

    def mutate[Context](self, k, v):
        ctx = copyContext(self)
        setattr(ctx, k, v)
        return ctx

def copyContext(ctx: Context):
    return Context.from_json(ctx.to_json())


DEFAULT = Context("", NamespaceStyle, True, IncludeRules(False), ClassRules(""))