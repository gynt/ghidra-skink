from typing import List

from skink.architecture.common.singleton import Singleton
from skink.architecture.common.exclusion import filter_includes
from skink.sarif.TypeInfo import TypeInfo
from skink.utils.OrderedSet import OrderedSet

from ...export.context import DEFAULT
from ...export.location import normalize_location, transform_location
from ...export.types import generate_include_for_type
from ...sarif.datatypes.DataTypeResult import DataTypeResult
from ...sarif.datatypes.StructField import StructField
from ...architecture.common.Field import Field
from dataclasses import dataclass, field

import re

@dataclass
class StructExportPart:
    fields: List[str] = field(default_factory = list)
    includes: List[str] = field(default_factory = list)


class Struct(object):

    def __init__(self, s: DataTypeResult, singleton: Singleton | None = None):
        self.loc = s.properties.additionalProperties.location
        self.ns = "::".join(v for v in self.loc.split("/") if v)
        self.name = s.properties.additionalProperties.name
        self.s = s
        self.singleton = singleton

    def namespace(self, ctx = DEFAULT):
        return transform_location(self.ns.replace("::", "/"), ctx).replace("/", "::")

    def location(self, ctx = DEFAULT):
        return transform_location(self.loc, ctx)

    def path(self, ctx = DEFAULT):
        return f"{self.location(ctx)}/{ctx.struct_rules.prefix}{self.name}{ctx.struct_rules.suffix}{ctx.include.file_extension}"

    def include(self, ctx = DEFAULT):
        return f'#include "{self.path(ctx)}"'
    
    def _collect_includes(self, ctx = DEFAULT):
        for name, field in self.s.properties.additionalProperties.fields.items():
            yield from generate_include_for_type(field.name, field.type, ctx=ctx)

    def includes(self, ctx = DEFAULT):
        return filter_includes(self._collect_includes(ctx), ctx)
    
    def export_field_declarations(self, ctx = DEFAULT):
        for n, sf in self.s.properties.additionalProperties.fields.items():
            f = Field(sf, name=n)
            yield f.declaration(ctx)

    def export_field_declarations_with_offsets_and_lengths(self, ctx = DEFAULT):
        # offset = 0, real offset = 0
        offset = 0
        for n, sf in self.s.properties.additionalProperties.fields.items():
            # 0 = 0 - 0
            # 1 = 5 - 4
            diff = sf.offset - offset
            if diff > 0:
                yield f"undefined1 padding_{hex(offset)}[{diff}]", offset, diff
            f = Field(sf, name=n)
            # 4 = 0 + 4
            offset = sf.offset + f.f.length
            yield f.declaration(ctx), f.f.offset, f.f.length
        # Do this once more if we haven't reached the end of the struct size yet:
        diff = self.s.properties.additionalProperties.size - offset
        if diff > 0:
            yield f"undefined1 padding_{hex(offset)}[{diff}]", offset, diff

    def export_fields(self, ctx = DEFAULT) -> StructExportPart:
        includes = self.includes(ctx = ctx)
        declarations = list(self.export_field_declarations())
        return StructExportPart(fields = declarations, includes = list(includes))

    def export(self, ctx = DEFAULT):
        includes = OrderedSet[str]()

        includes += self.includes(ctx=ctx)

        if ctx.style.namespace:
            namespaceWrap = lambda x: f"namespace {self.namespace(ctx)} {{\n\n  {x}\n\n}}"
        else:
            namespaceWrap = lambda x: x
        
        name = f"{ctx.struct_rules.prefix}{self.name}{ctx.struct_rules.suffix}"
        if ctx.struct_rules.typedef:
            structWrap = lambda x: f"typedef struct {name} {{\n\n    {x}\n\n  }} {name};"
        else:
            structWrap = lambda x: f"struct {name} {{\n\n    {x}\n\n  }};"

        declarations = list(self.export_field_declarations(ctx=ctx))

        return f"{"\n".join(includes)}\n\n{namespaceWrap(structWrap("\n\n    ".join(declarations)))}"