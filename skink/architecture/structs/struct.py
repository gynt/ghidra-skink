from typing import List

from ...export.context import DEFAULT
from ...export.location import ROOT, normalize_location, transform_location
from ...export.style import NamespaceStyle
from ...export.types import generate_include_for_type
from ...sarif.datatypes.DataTypeResult import DataTypeResult
from ...sarif.datatypes.StructField import StructField
from dataclasses import dataclass, field

@dataclass
class StructExportPart:
    fields: List[str] = field(default_factory = list)
    includes: List[str] = field(default_factory = list)

class Field(object):

    def __init__(self, f: StructField):
        self.f: StructField = f

    def declaration(self, ctx = DEFAULT):
        return f"{self.f.type.name} {self.f.field_name};"


class Struct(object):

    def __init__(self, s: DataTypeResult):
        loc = normalize_location(s.properties.additionalProperties.location)
        self.namespace = "::".join(v for v in loc.split("/") if v)
        self.location = loc
        self.name = s.properties.additionalProperties.name
        self.s = s

    def path(self, ctx = DEFAULT):
        return f"{self.location}/{ctx.struct_rules.prefix}{self.name}{ctx.struct_rules.suffix}.h"

    def include(self, ctx = DEFAULT):
        return f'#include "{self.path(ctx)}"'
    
    def _collect_includes(self, ctx = DEFAULT):
        for name, field in self.s.properties.additionalProperties.fields.items():
            yield from generate_include_for_type(field.name, field.type, ctx=ctx)

    def includes(self, ctx = DEFAULT):
        return self._collect_includes(ctx=ctx)
    
    def export_field_declarations(self, ctx = DEFAULT):
        for n, sf in self.s.properties.additionalProperties.fields.items():
            f = Field(sf)
            yield f.declaration(ctx)
    
    def export_fields(self, ctx = DEFAULT) -> StructExportPart:
        includes = self.includes(ctx = ctx)
        declarations = list(self.export_field_declarations())
        return StructExportPart(fields = declarations, includes = includes)

    def export(self, ctx = DEFAULT):
        includes = [
            # f'#include "{self.location}/{self.name}Struct.h"',
        ]

        includes += self.includes(ctx=ctx)

        if ctx.style == NamespaceStyle:
            namespaceWrap = lambda x: f"namespace {self.namespace} {{\n\n  {x}\n\n}}"
        else:
            namespaceWrap = lambda x: x
        
        name = f"{ctx.struct_rules.prefix}{self.name}{ctx.struct_rules.suffix}"
        if ctx.struct_rules.typedef:
            structWrap = lambda x: f"typedef struct {name} {{\n\n    {x}\n\n  }} {name};"
        else:
            structWrap = lambda x: f"struct {name} {{\n\n    {x}\n\n  }};"

        declarations = []
        for n, sf in self.s.properties.additionalProperties.fields.items():
            f = Field(sf)
            declarations.append(f.declaration(ctx))

        return f"{"\n".join(includes)}\n\n{namespaceWrap(structWrap("\n\n    ".join(declarations)))}"