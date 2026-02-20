
from dataclasses import dataclass, field
import logging
from typing import Dict, List

from skink.sarif.datatypes.EnumResult import EnumResult

SUFFICES = ["Byte", "Short", "Int"]

@dataclass(frozen=False)
class EnumFamily:
  name: str
  root: EnumResult | None = field(default=None)
  children: List[EnumResult] = field(default_factory=lambda: list())

def merge_constants_of_enum_family_members(ef: EnumFamily):
  if not ef.root or not ef.children:
    return
  rc = ef.root.properties.additionalProperties.constants
  for child in ef.children:
    for name, value in child.properties.additionalProperties.constants.items():
      if name in rc:
        if value != rc[name]:
          rc[f"NAME_CONFLICT__{child.properties.additionalProperties.name}_{name}"] = value
      else:
        rc[f"{child.properties.additionalProperties.name}__{name}"] = value

def collect_enum_families(objs, suffices = SUFFICES, default_root = "Int"):
  families: Dict[str, EnumFamily] = {}
  for obj in objs:
    if isinstance(obj, EnumResult):
      n = obj.properties.additionalProperties.name
      l = obj.properties.additionalProperties.location
      for suf in suffices:
        if n.endswith(suf):
          root_name = n[:-len(suf)]
          if root_name not in families:
            families[root_name] = EnumFamily(name=root_name)
          fam = families[root_name]
          if obj not in fam.children:
            fam.children.append(obj)
          break
      else:
        # no suffix found at the end of the name, must be root of family
        root_name = n
        if root_name not in families:
          families[root_name] = EnumFamily(name=root_name)
        fam = families[root_name]
        fam.root = obj
  orphans: List[EnumResult] = []
  for name, family in families.items():
    if family.root is not None and len(family.children) == 0:
      orphans.append(family.root)
      continue
    if family.root is None:
      for c in family.children:
        if c.properties.additionalProperties.name.endswith(default_root):
          family.root = c
          # TODO: can be child and root simultaneously, or family.children.remove(c) ?
          break
      else:
        logging.log(logging.WARN, f"no root member for enum family: {name}")
  families = {n: f for n, f in families.items() if f.root is not None and len(f.children) > 0}
  for name, family in families.items():
    merge_constants_of_enum_family_members(family)
  return list(families.values()), [o for o in objs if isinstance(o, EnumResult) and o in orphans]