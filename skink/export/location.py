from typing import Dict
from .context import DEFAULT

import re
patterns: Dict[str, re.Pattern] = {}

ROOT = '/'

def normalize_location(l: str, ctx = DEFAULT):
  if len(l) == 0:
    return l
  if l[0] == ROOT:
    l = l[1:]
  if l.endswith(".h"):
    l = l[:-len(".h")]
  elif l.endswith(".hpp"):
    l = l[:-len(".hpp")]
  return l

def transform_location(l: str, ctx = DEFAULT):
  l = normalize_location(l, ctx)
  tr = ctx.location_rules.transformation_rules
  if tr.use_mapping:
    mapping: Dict[str, str] = tr.mapping
    if l in mapping:
      return mapping[l]
    return l
  if tr.use_regex:
    changes = True
    while changes:
      for pat_string, repl_string in tr.regex.items():
        if not pat_string in patterns:
          patterns[pat_string] = re.compile(pat_string)
        pat = patterns[pat_string]
        l2 = re.sub(pat, repl_string, l)
        changes = l2 != l
        l = l2

  return l
