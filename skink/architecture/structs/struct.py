from typing import List

from skink.architecture.export.context import DEFAULT
from skink.architecture.export.style import NamespaceStyle
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

# TODO: copy pasted from function.py
    def _normalize_location(self, l: str):
        if l[0] == '/':
            if not l.startswith('/_HoldStrong'):
                l = 'EXE' + l
            else:
                l = l[1:]
        if l.endswith(".h"):
            l = l[:-2]
        return l
    
    def _include_for_type(self, field: StructField):
        t = field.type
        loc = t.location
        if not loc:
            raise Exception(f"no location for type: {field.name} {field.field_name}")
        
        if loc != "/": # TODO: is this too general?
            if loc.endswith(".h"):
                loc = self._normalize_location(loc)
                yield f'#include "{loc}.h"'
            else:
                loc = self._normalize_location(loc)
                name = t.name
                if name.endswith(" *"):
                    name = name[:-2]

                yield f'#include "{loc}/{name}.h"'


    # Note: includes return type sometimes
    def _collect_includes(self):
        for name, field in self.s.properties.additionalProperties.fields.items():
            yield from self._include_for_type(field)

    def includes(self):
        return self._collect_includes()

    def export(self, ctx = DEFAULT):
        includes = [
            # f'#include "{self.location}/{self.name}Struct.h"',
        ]

        includes += self.includes()

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