from skink.architecture.structs.struct import Struct
from skink.architecture.defineddata import DefinedData
from skink.sarif.symbols.symbol import SymbolResult
from skink.export.location import normalize_location, transform_location
from skink.utils.OrderedSet import OrderedSet
from ...export.context import DEFAULT, Context, FunctionRules
from ..functions import Function
from dataclasses import dataclass


from typing import List

@dataclass
class Singleton:
  defined_data: DefinedData
  sr: SymbolResult

class Class(object):

  def __init__(self, namespace: str, functions: List[Function], structure: Struct = None, singleton: Singleton = None):
    self.ns = namespace
    self.loc = namespace.replace("::", "/")
    self.baseloc = "/".join(self.loc.split("/")[:-1])
    self.name = self.loc.split("/")[-1]
    self.fs: List[Function] = []
    self.constructor: Function = None
    self.structure = structure
    self.singleton = singleton
    for f in functions:
      self.add_function(f)
    self.find_constructor()

  def find_constructor(self):
    if self.constructor:
      return self.constructor
    for f in self.fs:
      tn = f.f.properties.additionalProperties.ret.typeName
      if "*" in tn:
        if tn.replace("*", "").strip() == self.name:
          self.constructor = f
    

  def add_function(self, f: Function):
    self.fs.append(f)
    self.find_constructor()

  def functions(self, ctx = DEFAULT):
    for f in self.fs:
      if not ctx.class_rules.export_constructor:
        if f.namespace() == self.ns:
          if f == self.constructor: # "Constructor_" in f.name or
            # TODO: log warning message about this filtering
            continue
      yield f

  def namespace(self, ctx = DEFAULT):
    return transform_location(self.loc, ctx).replace("/", "::")

  def location(self, ctx = DEFAULT):
    return transform_location(self.loc, ctx)

  def path(self, ctx = DEFAULT):
    return f"{self.location(ctx)}/{ctx.class_rules.prefix}{self.name}{ctx.class_rules.suffix}.h"

  def export(self, ctx = DEFAULT):
    fr: FunctionRules = ctx.function_rules.mutate(include_convention = False)
    fr: FunctionRules = fr.mutate(include_this = False)
    ctx: Context = ctx.mutate(function_rules = fr)

    includes = OrderedSet()

    if self.structure:
      if not ctx.class_rules.inline_struct:
        includes.append(self.structure.include(ctx))
    else:
      includes.append(f'#include "{self.location(ctx)}/{self.name}{ctx.struct_rules.suffix}.h"')

    for f in self.functions(ctx):
      new_includes = list(f.includes(ctx))
      includes += new_includes

    if ctx.style.namespace:
      namespaceWrap = lambda x: f"namespace {self.namespace(ctx)} {{\n\n  {x}\n\n}}"
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
    
    for f in self.functions(ctx):
      declarations.append(f.declaration(ctx))

    return f"{"\n".join(includes)}\n\n{namespaceWrap(classWrap("\n\n    ".join(declarations)))}"