

from skink.architecture.common.exclusion import filter_includes
from skink.export.context import DEFAULT, Context
from skink.export.location import transform_location
from skink.export.types import generate_include_for_class, generate_include_for_type, generate_include_for_type_location
from skink.sarif.datatypes.TypedefResult import TypedefResult


class Typedef():
  def __init__(self, tr: TypedefResult):
    self.loc = tr.properties.additionalProperties.location
    self.ns = "::".join(v for v in self.loc.split("/") if v)
    self.name = tr.properties.additionalProperties.name
    self.tr = tr


  # Note: includes return type sometimes
  def _collect_includes(self, ctx = DEFAULT):
    if self.tr.properties.additionalProperties.typeName or self.tr.properties.additionalProperties.typeLocation:
      yield from generate_include_for_type_location(self.tr.properties.additionalProperties.typeName, self.tr.properties.additionalProperties.typeLocation, ctx=ctx)
    else:
      yield from generate_include_for_type(self.tr.properties.additionalProperties.name, self.tr.properties.additionalProperties.type, ctx=ctx)

  def includes(self, ctx = DEFAULT):
    return filter_includes(self._collect_includes(ctx), ctx)

  def location(self, ctx = DEFAULT):
    return transform_location(self.loc, ctx)

  def path(self, ctx = DEFAULT):
    return f"{self.location(ctx)}/{ctx.struct_rules.prefix}{self.name}{ctx.struct_rules.suffix}{ctx.include.file_extension}"

  def declaration(self, ctx: Context = DEFAULT):
    name = self.tr.properties.additionalProperties.name
    type = self.tr.properties.additionalProperties.type.name
    
    return f"typedef {type} {name};" # TODO: improve
  
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