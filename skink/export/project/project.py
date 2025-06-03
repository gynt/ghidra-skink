from typing import Any, Generator, Iterable, List
import ijson

from skink.sarif.BasicResult import BasicResult
from skink.sarif.decode_results import decode_result

from ..project.databases.symboldatabase import SymbolDatabase
from ...sarif.symbols.symbol import SymbolResult

import pathlib

from ...logger import log, logging

def promote_pathstring(path: str | pathlib.Path):
  if isinstance(path, pathlib.Path):
    return path
  return pathlib.Path(path).absolute()

class Project(object):
  
  def __init__(self, path: pathlib.Path | str | None = None, paths: Iterable[str] | Iterable[pathlib.Path] | None = None, objects: Iterable[BasicResult] | None = None):
    self.paths: List[pathlib.Path] = list()
    self.objects = None
    if path:
      self.paths = [promote_pathstring(path)]
    elif paths:
      self.paths = list(promote_pathstring(p) for p in paths)
    elif objects:
      self.objects = objects
    self.symdb = SymbolDatabase()
    self.counts = {'total': 0, 'member': 0, 'class': 0, 'namespace': 0}

  def reset_counts(self):
    self.counts = {'total': 0, 'member': 0, 'class': 0, 'namespace': 0}    

  def yield_objects(self) -> Iterable[Any]:
    if self.objects:
      yield from self.objects
    if self.objects:
      return
    for path in self.paths:
      with open(path, 'r') as f:
        yield from ijson.items(f, 'runs.item.results.item')

  def yield_decoded_objects(self, debug=False) -> Iterable[BasicResult]:
    for obj in self.yield_objects():
      if debug:
        log(logging.DEBUG, obj)
      yield decode_result(obj)

  def process_symbol_results(self, yield_filters = ['address'], prefix = "", permit_overwrite = False, drop_submembers = True, store_symbol_result = False) -> Generator[SymbolResult]:
    if not self.paths:
      raise Exception(f"no paths set: {self.paths}")
    
    self.reset_counts()
    
    for obj in self.yield_objects():
      if obj['ruleId'] == 'SYMBOLS':
        sr: SymbolResult = SymbolResult.from_dict(obj) # type: ignore
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
        
        if self.symdb.add_entry(f"{l}{n}", k, a, e, extra=sr if store_symbol_result else None, permit_overwrite=permit_overwrite):
          self.counts['total'] += 1
          self.counts[k] += 1

        if 'address' in yield_filters:
          if len(sr.locations) == 0:
            continue
          if sr.locations[0].physicalLocation.address.absoluteAddress == 0:
            continue
        
        yield sr

  def process_all_symbol_results(self, *args, **kwargs):
    for _ in self.process_symbol_results(*args, **kwargs):
      continue