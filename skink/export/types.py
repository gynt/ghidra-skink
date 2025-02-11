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

            yield f'#include "{loc}/{type_name}.h"'