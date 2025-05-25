from .context import DEFAULT
from .location import ROOT, transform_location
from ..sarif.TypeInfo import TypeInfo


def generate_include_for_type(type_name: str, type_info: TypeInfo, ctx = DEFAULT):
    loc = type_info.location
    if not loc:
        raise Exception(f"no location for type: {type_name}")
    
    # Some types are available globally, no include is necessary
    assumeGlobal = loc == ROOT
    if not assumeGlobal:
        if loc.endswith(".h"):
            loc = transform_location(loc, ctx)
            yield f'#include "{loc}.h"'
        else:
            loc = transform_location(loc, ctx)
            if type_name.endswith(" *"):
                type_name = type_name[:-2]
            if "[" in type_name and type_name.endswith("]"):
                s = type_name.index("[")
                f = type_name.index("]")
                if f < s:
                    raise Exception()
                type_name = type_name[:s] + type_name[(f+1):]

            yield f'#include "{loc}/{type_name}.h"'


def generate_include_for_class(type_name: str, type_info: TypeInfo, ctx = DEFAULT):
    name = type_name.replace(" *", "")
    ti: TypeInfo = TypeInfo.from_json(type_info.to_json())
    # TODO: is this the right place to do this?
    if ctx.promote_to_class:
        ti.location += f"/{name}"
        return generate_include_for_type(f"{ctx.class_rules.prefix}{name}{ctx.class_rules.suffix}", type_info=ti, ctx=ctx)
    return generate_include_for_type(f"{name}", type_info=ti, ctx=ctx)