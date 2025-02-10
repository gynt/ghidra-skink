from skink.architecture.export.context import DEFAULT, FunctionRules
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
        ctx = ctx.mutate(function_rules = fr)

        includes = [
            f'#include "{self.location}/{self.name}Struct.h"',
        ]

        for f in self.functions:
            includes += f.includes(False)

        if ctx.style == NamespaceStyle:
            namespaceWrap = lambda x: f"namespace {self.namespace} {{\n\n  {x}\n\n}}"
        else:
            namespaceWrap = lambda x: x

        classWrap = lambda x: f"class {ctx.class_rules.prefix}{self.name}Class : struct {self.name}Struct {{\n\n    {x}\n\n  }}"

        declarations = []
        for f in self.functions:
            declarations.append(f.declaration(ctx))

        return f"{"\n".join(includes)}\n\n{namespaceWrap(classWrap("\n\n    ".join(declarations)))}"