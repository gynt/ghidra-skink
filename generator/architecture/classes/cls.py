from generator.architecture.export.context import DEFAULT
from generator.architecture.export.style import NamespaceStyle
from generator.architecture.functions import Function


from typing import List


class Class(object):

    def __init__(self, namespace: str, functions: List[Function]):
        self.namespace = namespace
        self.location = namespace.replace("::", "/")
        self.name = self.location.split("/")[-1]
        self.functions = functions

    def export(self, ctx = DEFAULT):
        ctx = ctx.mutate("functions_virtual", True)

        includes = [
            f'#include "{self.location}/{self.name}Struct.h"',
        ]

        for f in self.functions:
            includes += f.includes(False)

        if ctx.style == NamespaceStyle:
            namespaceWrap = lambda x: f"namespace {self.namespace} {{\n\n\t{x}\n\n}}"
        else:
            namespaceWrap = lambda x: x

        classWrap = lambda x: f"class {ctx.class_rules.prefix}{self.name}Class : struct {self.name}Struct {{\n\n\t\t{x}\n\n\t}}"

        declarations = []
        for f in self.functions:
            declarations.append(f.declaration(ctx))

        return f"{"\n".join(includes)}\n\n{namespaceWrap(classWrap("\n\n\t\t".join(declarations)))}"