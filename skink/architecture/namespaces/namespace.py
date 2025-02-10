from typing import Any, List
from skink.architecture.export.context import DEFAULT, Context
from skink.architecture.export.style import NamespaceStyle
from skink.architecture.functions.function import Function


class Namespace(object):
    
    def __init__(self, namespace: str, functions: List[Function]):
        self.namespace = namespace
        self.location = namespace.replace("::", "/")
        self.name = self.location.split("/")[-1]
        self.functions = functions

    def export(self, ctx = DEFAULT):
        includes = [
            f'#include "{self.location}/{self.name}Class.h"',
            f'#include "{self.location}/{self.name}Struct.h"',
        ]

        for f in self.functions:
            includes += f.includes(False)

        if ctx.style == NamespaceStyle:
            wrap = lambda x: f"namespace {self.namespace} {{\n\n  {x}\n\n}}"
        else:
            wrap = lambda x: x

        declarations = []
        for f in self.functions:
            declarations.append(f.declaration(ctx))

        return f"{"\n".join(includes)}\n\n{wrap("\n\n  ".join(declarations))}"