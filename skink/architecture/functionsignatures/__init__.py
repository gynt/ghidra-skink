

from skink.export.context import DEFAULT, Context
from skink.export.location import transform_location
from skink.export.types import generate_include_for_class, generate_include_for_type
from skink.sarif.datatypes.FunctionSignatureResult import FunctionSignatureResult


class FunctionSignature():
  def __init__(self, fsr: FunctionSignatureResult):
    self.loc = fsr.properties.additionalProperties.location
    self.ns = "::".join(v for v in self.loc.split("/") if v)
    self.name = fsr.properties.additionalProperties.name
    self.fsr = fsr


  # Note: includes return type sometimes
  def _collect_includes(self, ctx = DEFAULT):
    for param in self.fsr.properties.additionalProperties.params:  
        yield from generate_include_for_type(param.name, param, ctx=ctx)
    
    param = self.fsr.properties.additionalProperties.retType
    yield from generate_include_for_type(param.name, param, ctx=ctx)

  def includes(self, ctx = DEFAULT):
    return self._collect_includes(ctx)

  def location(self, ctx = DEFAULT):
    return transform_location(self.loc, ctx)

  def path(self, ctx = DEFAULT):
    return f"{self.location(ctx)}/{ctx.struct_rules.prefix}{self.name}{ctx.struct_rules.suffix}.h"

  def declaration(self, ctx: Context = DEFAULT):
    name = self.fsr.properties.additionalProperties.name
    retTypeName = self.fsr.properties.additionalProperties.retType.name

    callingConvention = self.fsr.properties.additionalProperties.callingConventionName
    params = [param for param in self.fsr.properties.additionalProperties.params]
    
    # these only have type names, no function argument names
    all_params = ", ".join([f"{param.name} " for param in params])
    
    return f"typedef {retTypeName} {callingConvention} {name}({all_params});" # TODO: improve
  
  def namespace(self, ctx = DEFAULT):
    return transform_location(self.ns.replace("::", "/"), ctx).replace("/", "::")
  
  def __str__(self):
    includes: str = "\n".join(self._collect_includes())
    declaration: str = self.declaration()

    return '\n\n'.join([includes, declaration])
  
  def export(self, ctx = DEFAULT):
    
    if ctx.style.namespace:
      wrap = lambda x: f"namespace {self.namespace()} {{\n\n  {x}\n\n}}"
    else:
      wrap = lambda x: x

    return f"{"\n".join(self.includes(ctx))}\n\n{wrap(self.declaration(ctx))}"