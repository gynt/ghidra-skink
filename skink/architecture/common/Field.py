

from skink.architecture.utils import extract_array_part
from skink.export.context import DEFAULT
from skink.export.types import remap_type
from skink.sarif.datatypes.StructField import StructField
from skink.sarif.datatypes.UnionResult import UnionField
from .sanitization import sanitize_name


class Field(object):

    def __init__(self, f: UnionField|StructField, name: str = ""):
        self.f = f
        self.name = name
        #if name:
            # TODO: this is too dirty, improve
            #self.f.field_name = name

    def declaration(self, ctx = DEFAULT):
        eol = ""
        if ctx.struct_rules.field_eol_char:
            eol = ";"
        name = sanitize_name(self.name if self.name else self.f.field_name)
        if self.f.type.kind == "array":
            c = self.f.type.count
            array_part = extract_array_part(self.f.type.name)
            tname = self.f.type.name.replace(array_part, "", 1)
            type_name, type_loc = remap_type(type_name=tname, type_loc=self.f.type.location, ctx=ctx)
            fname = name + array_part
            return f"{type_name} {fname}{eol}"
        if self.f.name.endswith("]"):
            array_part = extract_array_part(self.f.name)
            tname = self.f.name.replace(array_part, "", 1)
            type_name, type_loc = remap_type(type_name=tname, type_loc=self.f.type.location, ctx=ctx)
            fname = name + array_part
            return f"{type_name} {fname}{eol}"
        tname = self.f.type.name
        type_name, type_loc = remap_type(type_name=tname, type_loc=self.f.type.location, ctx=ctx)
        if self.f.type.kind == 'pointer' and "*" not in tname:
            type_name += " *"
        return f"{type_name} {name}{eol}"
