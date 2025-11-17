from dataclasses import dataclass, field
from typing import Dict, List
from warnings import deprecated

from dataclasses_json import dataclass_json, DataClassJsonMixin

@dataclass
class AbstractContext(DataClassJsonMixin):
    def copy(self) -> "AbstractContext":
        return self.from_json(self.to_json())

    @deprecated("mutate() is deprecated")
    def mutate(self, **kwargs) -> "AbstractContext":
        ctx = self.copy()
        for k,v  in kwargs.items():
          if not hasattr(ctx, k):
              raise Exception(f"Context {ctx} does not have attribue {k}")
          setattr(ctx, k, v)
        return ctx


@dataclass
class IncludeRules(AbstractContext):
    functions_this_parameter_type: bool = False
    prefix_include: bool = True
    file_extension: str = ".hpp"
    exclude: list[str] = field(default_factory=lambda: list[str](["WinDef[.]h", "winnt[.]h", "ntddk_32/.*", "^.+?[.]h$"]))
    exclude_use_regex: bool = True

    def copy(self) -> "IncludeRules":
        return self.from_json(self.to_json())

@dataclass
class ClassRules(AbstractContext):
    prefix: str = ""
    suffix: str = "Class"
    inline_struct: bool = False
    export_constructor: bool = False
    virtual: bool = False
    class_as_namespace: bool = True

    def copy(self) -> "ClassRules":
        return self.from_json(self.to_json())

@dataclass
class FunctionRules(AbstractContext):
    include_convention: bool = True
    include_this: bool = True

    def copy(self) -> "FunctionRules":
        return self.from_json(self.to_json())

@dataclass
class StructRules(AbstractContext):
    prefix: str = ""
    typedef: bool = False
    suffix: str = "Struct"
    field_eol_char: bool = True

    def copy(self) -> "StructRules":
        return self.from_json(self.to_json())

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

    def copy(self) -> "TransformationRules":
        return self.from_json(self.to_json())

@dataclass
class LocationRules(AbstractContext):
    transformation_rules: TransformationRules = field(default_factory=lambda: TransformationRules())

    def copy(self) -> "LocationRules":
        return self.from_json(self.to_json())

@dataclass
class StyleRules(AbstractContext):
    namespace: bool = True

    def copy(self) -> "StyleRules":
        return self.from_json(self.to_json())

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

    def copy(self) -> "Context":
        return self.from_json(self.to_json())

DEFAULT = Context()