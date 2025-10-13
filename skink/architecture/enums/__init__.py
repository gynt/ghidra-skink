
from skink.export.context import DEFAULT
from skink.export.location import transform_location
from skink.sarif.datatypes.EnumResult import EnumResult


class Enum(object):
  def __init__(self, er: EnumResult):
    self.loc = er.properties.additionalProperties.location
    self.ns = "::".join(v for v in self.loc.split("/") if v)
    self.name = er.properties.additionalProperties.name
    self.er = er

  def namespace(self, ctx = DEFAULT):
    return transform_location(self.ns.replace("::", "/"), ctx).replace("/", "::")

  def location(self, ctx = DEFAULT):
    return transform_location(self.loc, ctx)

  def path(self, ctx = DEFAULT):
    return f"{self.location(ctx)}/{self.name}{ctx.include.file_extension}"