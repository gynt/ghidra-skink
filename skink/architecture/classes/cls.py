from skink.architecture.export.context import DEFAULT, Context, FunctionRules
from skink.architecture.export.style import NamespaceStyle
from skink.architecture.functions import Function


from typing import List


class Class(object):

    def __init__(self, namespace: str, functions: List[Function]):
        self.namespace = namespace
        self.location = namespace.replace("::", "/")
        self.name = self.location.split("/")[-1]
        self.functions = functions

    def export(self, ctx = DEFAULT):
        fr: FunctionRules = ctx.function_rules.mutate(include_convention = False)
        fr: FunctionRules = fr.mutate(include_this = False)
        ctx: Context = ctx.mutate(function_rules = fr)

        includes = [
            f'#include "{self.location}/{self.name}{ctx.struct_rules.suffix}.h"',
        ]

        for f in self.functions:
            includes += f.includes(False)

        if ctx.style == NamespaceStyle:
            namespaceWrap = lambda x: f"namespace {self.namespace} {{\n\n  {x}\n\n}}"
        else:
            namespaceWrap = lambda x: x

        className = f"{ctx.class_rules.prefix}{self.name}{ctx.class_rules.suffix}"
        structName = f"{ctx.struct_rules.prefix}{self.name}{ctx.struct_rules.suffix}"
        classWrap = lambda x: f"class {className} : struct {structName} {{\n\n    {x}\n\n  }}"

        declarations = []
        for f in self.functions:
            declarations.append(f.declaration(ctx))

        return f"{"\n".join(includes)}\n\n{namespaceWrap(classWrap("\n\n    ".join(declarations)))}"