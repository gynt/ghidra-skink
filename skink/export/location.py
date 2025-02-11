from typing import Dict
from .context import DEFAULT

ROOT = '/'

def normalize_location(l: str, ctx = DEFAULT):
    if l[0] == ROOT:
        l = l[1:]
    if l.endswith(".h"):
        l = l[:-2]
    return l

def transform_location(l: str, ctx = DEFAULT):
    l = normalize_location(l, ctx)
    tr = ctx.location_rules.transformation_rules
    if tr.use_mapping:
        mapping: Dict[str, str] = tr.mapping
        if l in mapping:
            return mapping[l]
        return l
    return l
