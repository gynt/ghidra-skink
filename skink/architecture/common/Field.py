

from skink.architecture.utils import extract_array_part
from skink.export.context import DEFAULT
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
            fname = name + array_part
            return f"{tname} {fname}{eol}"
        return f"{self.f.type.name} {name}{eol}"
