from typing import List

from skink.architecture.export.context import DEFAULT
from skink.architecture.export.location import ROOT, transform_location
from skink.architecture.export.style import NamespaceStyle
from skink.architecture.export.types import generate_include_for_type
from skink.sarif import DataTypeResult, StructField

class Field(object):

    def __init__(self, f: StructField):
        self.f: StructField = f

    def declaration(self, ctx = DEFAULT):
        return f"{self.f.type.name} {self.f.field_name};"


class Struct(object):

    def __init__(self, s: DataTypeResult):
        self.namespace = "::".join(v for v in s.properties.additionalProperties.location.split("/") if v)
        self.location = s.properties.additionalProperties.location
        self.name = s.properties.additionalProperties.name
        self.s = s
    
    def _collect_includes(self, ctx = DEFAULT):
        for name, field in self.s.properties.additionalProperties.fields.items():
            yield from generate_include_for_type(field.name, field.type, ctx=ctx)

    def includes(self, ctx = DEFAULT):
        return self._collect_includes(ctx=ctx)

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