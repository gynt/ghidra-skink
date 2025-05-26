from dataclasses import dataclass, field
from typing import Dict, List

from dataclasses_json import dataclass_json

@dataclass_json
@dataclass
class AbstractContext(object):

    def copy(self) -> "AbstractContext":
        return self.from_json(self.to_json())

    def mutate(self, **kwargs) -> "AbstractContext":
        ctx = self.copy()
        for k,v  in kwargs.items():
          if not hasattr(ctx, k):
              raise Exception(f"Context {ctx} does not have attribue {k}")
          setattr(ctx, k, v)
        return ctx


@dataclass_json
@dataclass
class IncludeRules(AbstractContext):
    functions_this_parameter_type: bool = False


@dataclass_json
@dataclass
class ClassRules(AbstractContext):
    prefix: str = ""
    suffix: str = "Class"
    inline_struct: bool = False
    export_constructor: bool = False

@dataclass_json
@dataclass
class FunctionRules(AbstractContext):
    virtual: bool = False
    include_convention: bool = True
    include_this: bool = True

@dataclass_json
@dataclass
class StructRules(AbstractContext):
    prefix: str = ""
    typedef: bool = False
    suffix: str = "Struct"

@dataclass_json
@dataclass
class TransformationRules(AbstractContext):
    use_regex: bool = False
    regex: Dict[str, str] = field(default_factory=dict)
    use_mapping: bool = False
    mapping: Dict[str, str] = field(default_factory=dict)
    use_include_list: bool = False
    include_list: List[str] = field(default_factory=list)
    use_exclude_list: bool = False
    exclude_list: List[str] = field(default_factory=list)

@dataclass_json
@dataclass
class LocationRules(AbstractContext):
    transformation_rules: TransformationRules = field(default_factory=lambda: TransformationRules())

@dataclass_json
@dataclass
class StyleRules(AbstractContext):
    namespace: bool = True

@dataclass_json
@dataclass
class Context(AbstractContext):
    root: str = ""
    style: StyleRules = field(default_factory=lambda: StyleRules())
    promote_to_class: bool = True
    include: IncludeRules = field(default_factory=lambda: IncludeRules())
    function_rules: FunctionRules = field(default_factory=lambda: FunctionRules())
    class_rules: ClassRules = field(default_factory=lambda: ClassRules())
    struct_rules: StructRules = field(default_factory=lambda: StructRules())
    location_rules: LocationRules = field(default_factory=lambda: LocationRules())


DEFAULT = Context()