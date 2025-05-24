from typing import Generator
import ijson

from ..project.databases.symboldatabase import SymbolDatabase
from ...sarif.symbols.symbol import SymbolResult


class Project(object):
  
  def __init__(self, path: str | None = None):
    self.path = path
    self.symdb = SymbolDatabase()

  def process_symbol_results(self, filters = ['address'], prefix = "", permit_overwrite = False, drop_submembers = True) -> Generator[SymbolResult]:
    if not self.path:
      raise Exception(f"no path set: {self.path}")
    
    with open(self.path, 'r') as f:
      for obj in ijson.items(f, 'runs.item.results.item'):
        if obj['ruleId'] == 'SYMBOLS':
          sr: SymbolResult = SymbolResult.from_dict(obj)
          n = sr.properties.additionalProperties.name
          l = sr.properties.additionalProperties.location
          if prefix:
            if not l.startswith(f"{prefix}::"):
              if l != '' or n != prefix:
                continue
          a = sr.locations[0].physicalLocation.address.absoluteAddress
          e = sr.properties.additionalProperties.kind == 'external'
          k = sr.properties.additionalProperties.type
          if not k and sr.properties.additionalProperties.namespaceIsClass:
            k = 'member'
          
          if drop_submembers:
            sp = l[:-2]
            if self.symdb.has(sp):
              if self.symdb.get(sp).kind == 'member':
                continue

          self.symdb.add_entry(f"{l}{n}", k, a, e, extra=sr, permit_overwrite=permit_overwrite)

          if 'address' in filters:
            if len(sr.locations) == 0:
              continue
            if sr.locations[0].physicalLocation.address.absoluteAddress == 0:
              continue
          yield sr

  def process_all_symbol_results(self, *args, **kwargs):
    for _ in self.process_symbol_results(*args, **kwargs):
      continue