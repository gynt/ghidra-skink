from typing import List

from skink.architecture.structs.struct import Struct
from skink.utils.OrderedSet import OrderedSet
from ...export.context import DEFAULT
from ...architecture.functions.function import Function


class Namespace(object):
    
    # TODO: implement structures
    def __init__(self, namespace: str, functions: List[Function], structures: List[Struct] = None):
        self.namespace = namespace
        self.location = namespace.replace("::", "/")
        self.name = self.location.split("/")[-1]
        self.functions = functions
        for f in self.functions:
            if f.namespace() != self.namespace:
                raise Exception(f"namespace of function ({f.namespace()}) is not same as Namespace {self.namespace}")

    def path(self, ctx = DEFAULT):
        return f"{self.location}/{self.name}{ctx.include.file_extension}"

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