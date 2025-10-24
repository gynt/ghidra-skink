from .context import DEFAULT
from .location import ROOT, transform_location
from ..sarif.TypeInfo import TypeInfo


def repair_asterisk(type_name: str):
  while type_name[-1] == "*" or type_name[-1] == " ":
    type_name = type_name[:-1]
  return type_name

def repair_indexing(type_name: str):
  while '[' in type_name and ']' in type_name:
    s = type_name.index("[")
    f = type_name.index("]", s) # note: ] should come after [
    type_name = type_name[:s] + type_name[(f+1):]
  return type_name

def generate_include_for_type(type_name: str, type_info: TypeInfo, ctx = DEFAULT):
  loc = type_info.location
  if not loc:
    raise Exception(f"no location for type: {type_name}")
  
  # Some types are available globally, no include is necessary
  assumeGlobal = loc == ROOT
  if not assumeGlobal:
    if loc.endswith(".h"):
      loc = transform_location(loc, ctx)
      result = f"{loc}.h"
      if ctx.include.prefix_include:
        result = f'#include "{result}"'
      yield result
    elif loc.endswith(".hpp"):
      loc = transform_location(loc, ctx)
      result = f"{loc}.hpp"
      if ctx.include.prefix_include:
        result = f'#include "{result}"'
      yield result
    else:
      loc = transform_location(loc, ctx)

      type_name = repair_asterisk(type_name)
      type_name = repair_indexing(type_name)
      result = f"{loc}/{type_name}{ctx.include.file_extension}"
      if ctx.include.prefix_include:
        result = f'#include "{result}"'
      yield result


def generate_include_for_class(type_name: str, type_info: TypeInfo, ctx = DEFAULT):
  name = type_name.replace(" *", "")
  ti: TypeInfo = TypeInfo.from_json(type_info.to_json())
  # TODO: is this the right place to do this?
  if ctx.promote_to_class:
    ti.location += f"/{name}"
    return generate_include_for_type(f"{ctx.class_rules.prefix}{name}{ctx.class_rules.suffix}", type_info=ti, ctx=ctx)
  return generate_include_for_type(f"{name}", type_info=ti, ctx=ctx)