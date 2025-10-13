from typing import List

from skink.sarif.TypeInfo import TypeInfo
from skink.utils.OrderedSet import OrderedSet

from ...export.context import DEFAULT
from ...export.location import normalize_location, transform_location
from ...export.types import generate_include_for_type
from ...sarif.datatypes.DataTypeResult import DataTypeResult
from ...sarif.datatypes.UnionResult import UnionField, UnionResult
from ...sarif.datatypes.StructField import StructField
from dataclasses import dataclass, field

@dataclass
class UnionExportPart:
    fields: List[str] = field(default_factory = list)
    includes: List[str] = field(default_factory = list)

class Field(object):

    def __init__(self, f: UnionField, name: str = ""):
        self.f: UnionField = f
        self.name = name
        #if name:
            # TODO: this is too dirty, improve
            #self.f.field_name = name

    def declaration(self, ctx = DEFAULT):
        eol = ""
        if ctx.struct_rules.field_eol_char:
            eol = ";"
        name = self.name if self.name else self.f.field_name
        if self.f.type.kind == "array":
            c = self.f.type.count
            tname = self.f.type.name.replace(f"[{c}]", "", 1)
            fname = name + f"[{c}]"
            return f"{tname} {fname}{eol}"
        return f"{self.f.type.name} {name}{eol}"


class Union(object):

    def __init__(self, s: UnionResult):
        self.loc = s.properties.additionalProperties.location
        self.ns = "::".join(v for v in self.loc.split("/") if v)
        self.name = s.properties.additionalProperties.name
        self.s = s

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
        return self._collect_includes(ctx=ctx)
    
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

    def export_fields(self, ctx = DEFAULT) -> UnionExportPart:
        includes = self.includes(ctx = ctx)
        declarations = list(self.export_field_declarations())
        return UnionExportPart(fields = declarations, includes = includes)

    def export(self, ctx = DEFAULT):
        includes = OrderedSet()

        includes += self.includes(ctx=ctx)

        if ctx.style.namespace:
            namespaceWrap = lambda x: f"namespace {self.namespace(ctx)} {{\n\n  {x}\n\n}}"
        else:
            namespaceWrap = lambda x: x
        
        name = f"{ctx.struct_rules.prefix}{self.name}{ctx.struct_rules.suffix}"
        if ctx.struct_rules.typedef:
            structWrap = lambda x: f"typedef union {name} {{\n\n    {x}\n\n  }} {name};"
        else:
            structWrap = lambda x: f"union {name} {{\n\n    {x}\n\n  }};"

        declarations = list(self.export_field_declarations(ctx=ctx))

        return f"{"\n".join(includes)}\n\n{namespaceWrap(structWrap("\n\n    ".join(declarations)))}"