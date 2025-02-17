from typing import Any, List

from skink.utils.OrderedSet import OrderedSet
from ...export.context import DEFAULT, Context
from ...export.style import NamespaceStyle
from ...architecture.functions.function import Function


class Namespace(object):
    
    def __init__(self, namespace: str, functions: List[Function]):
        self.namespace = namespace
        self.location = namespace.replace("::", "/")
        self.name = self.location.split("/")[-1]
        self.functions = functions

    def path(self, ctx = DEFAULT):
        return f"{self.location}/{self.name}.h"

    def export(self, ctx = DEFAULT):
        includes = OrderedSet()

        for f in self.functions:
            includes += f.includes(ctx)

        if ctx.style.namespace:
            wrap = lambda x: f"namespace {self.namespace} {{\n\n  {x}\n\n}}"
        else:
            wrap = lambda x: x

        declarations = []
        for f in self.functions:
            declarations.append(f.declaration(ctx))

        return f"{"\n".join(includes)}\n\n{wrap("\n\n  ".join(declarations))}"