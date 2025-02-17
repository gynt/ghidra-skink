from skink.architecture.structs.struct import Struct
from skink.utils.OrderedSet import OrderedSet
from ...export.context import DEFAULT, Context, FunctionRules
from ...export.style import NamespaceStyle
from ..functions import Function


from typing import List


class Class(object):

    def __init__(self, namespace: str, functions: List[Function], structure: Struct = None):
        self.namespace = namespace
        self.location = namespace.replace("::", "/")
        self.name = self.location.split("/")[-1]
        self.functions = functions
        self.structure = structure

    def path(self, ctx = DEFAULT):
        return f"{self.location}/{ctx.class_rules.prefix}{self.name}{ctx.class_rules.suffix}.h"

    def export(self, ctx = DEFAULT):
        fr: FunctionRules = ctx.function_rules.mutate(include_convention = False)
        fr: FunctionRules = fr.mutate(include_this = False)
        ctx: Context = ctx.mutate(function_rules = fr)

        includes = OrderedSet()

        if self.structure:
            if not ctx.class_rules.inline_struct:
                includes.append(self.structure.include())
        else:
            includes.append(f'#include "{self.location}/{self.name}{ctx.struct_rules.suffix}.h"')

        for f in self.functions:
            includes += f.includes(ctx)

        if ctx.style == NamespaceStyle:
            namespaceWrap = lambda x: f"namespace {self.namespace} {{\n\n  {x}\n\n}}"
        else:
            namespaceWrap = lambda x: x

        className = f"{ctx.class_rules.prefix}{self.name}{ctx.class_rules.suffix}"
        structName = f"{ctx.struct_rules.prefix}{self.name}{ctx.struct_rules.suffix}"
        # TODO: make this inheritance from struct optional
        if ctx.class_rules.inline_struct:
            classWrap = lambda x: f"class {className} {{\n\n    {x}\n\n  }}"
        else:
            classWrap = lambda x: f"class {className} : struct {structName} {{\n\n    {x}\n\n  }}"

        fields = []
        if ctx.class_rules.inline_struct:
            sep = self.structure.export_fields(ctx)
            for f in sep.fields:
                fields.append(f)
            for i in sep.includes:
                includes.append(i)

        declarations = []
        if ctx.class_rules.inline_struct:
            declarations += fields
        
        for f in self.functions:
            declarations.append(f.declaration(ctx))

        return f"{"\n".join(includes)}\n\n{namespaceWrap(classWrap("\n\n    ".join(declarations)))}"