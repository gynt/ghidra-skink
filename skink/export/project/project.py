from typing import Any, Generator, Iterable, List
import ijson, json

from skink.sarif.BasicResult import BasicResult
from skink.sarif.decode_results import decode_result

from ..project.databases.symboldatabase import SymbolDatabase
from ...sarif.symbols.symbol import SymbolResult
from ...sarif.functions.FunctionResult import FunctionResult
from ...sarif.datatypes.DataTypeResult import DataTypeResult
from ...sarif.defineddata.DefinedDataResult import DefinedDataResult

import pathlib

from ...logger import log, logging

def log_ijson_backend():
  log(logging.DEBUG, f"ijson: using backend {ijson.backend_name}")

def promote_pathstring(path: str | pathlib.Path):
  if isinstance(path, pathlib.Path):
    return path
  return pathlib.Path(path).absolute()

class Project(object):
  
  def __init__(self, path: pathlib.Path | str | None = None, paths: Iterable[str] | Iterable[pathlib.Path] | None = None, objects: Iterable[Any] | None = None):
    self.paths: List[pathlib.Path] = list()
    self.objects = None
    if path:
      self.paths = [promote_pathstring(path)]
    elif paths:
      self.paths = list(promote_pathstring(p) for p in paths)
    elif objects:
      self.objects = objects
    self.symdb = SymbolDatabase()
    self.counts = {'total': 0, 'member': 0, 'class': 0, 'namespace': 0, 'unknown': 0}

  def save_project(self, path: str | pathlib.Path):
    items = list(obj.to_dict() for obj in self.yield_raw_objects())
    pathlib.Path(path).write_text(json.dumps({
      "runs": [{
        "results": items
      }]
    }))

  @staticmethod
  def load_saved_project(path: str | pathlib.Path):
    return Project(path = path)

  def reset_counts(self):
    self.counts = {'total': 0, 'member': 0, 'class': 0, 'namespace': 0, 'unknown': 0}    

  def yield_raw_objects(self) -> Generator[Any]:
    if self.objects:
      yield from self.objects
    if self.objects:
      return
    for path in self.paths:
      with open(path, 'r') as f:
        yield from ijson.items(f, 'runs.item.results.item')

  def yield_objects(self, debug=False) -> Generator[BasicResult]:
    for obj in self.yield_raw_objects():
      if debug:
        log(logging.DEBUG, obj)
      yield decode_result(obj)

  def process_symbol_results(self, yield_filters = ['address'], prefix = "", permit_overwrite = False, drop_submembers = True, store_symbol_result = False) -> Generator[SymbolResult]:
    if not self.paths:
      raise Exception(f"no paths set: {self.paths}")
    
    self.reset_counts()
    
    for obj in self.yield_raw_objects():
      if obj['ruleId'] == 'SYMBOLS':
        sr: SymbolResult = SymbolResult.from_dict(obj) # type: ignore
        log(logging.DEBUG, sr)
        n = sr.properties.additionalProperties.name
        l = sr.properties.additionalProperties.location
        g = not l
        if prefix:
          if not l.startswith(f"{prefix}::"):
            if l != '' or n != prefix:
              continue
        a = sr.locations[0].physicalLocation.address.absoluteAddress
        e = sr.properties.additionalProperties.kind == 'external'
        k = sr.properties.additionalProperties.type
        if not k and sr.properties.additionalProperties.namespaceIsClass:
          k = 'member'
        elif not k:
          sp = l[:-2] # remove trailing "::"
          if sp and self.symdb.has(sp):
            if self.symdb.get(sp).kind == "namespace":
              k = 'member'
        
        if drop_submembers:
          sp = l[:-2]
          if sp and self.symdb.has(sp):
            if self.symdb.get(sp).kind == 'member':
              continue
        
        if self.symdb.add_entry(path=f"{l}{n}", 
                                kind=k, 
                                address=a, 
                                external=e, 
                                extra=sr if store_symbol_result else None,
                                permit_overwrite=permit_overwrite):
          self.counts['total'] += 1
          if k in self.counts:
            self.counts[k] += 1
          else:
            self.counts['unknown'] += 1

        if 'address' in yield_filters:
          if len(sr.locations) == 0:
            continue
          if sr.locations[0].physicalLocation.address.absoluteAddress == 0:
            continue
        
        yield sr

  def process_all_symbol_results(self, *args, **kwargs):
    for _ in self.process_symbol_results(*args, **kwargs):
      continue

  def find_symbols_for_address(self, address: int) -> Generator[BasicResult]:
    for obj in self.yield_raw_objects():
      ruleId = obj['ruleId']
      if ruleId == 'SYMBOLS':
        sr: SymbolResult = SymbolResult.from_dict(obj) # type: ignore
        srLocations = [loc.physicalLocation.address.absoluteAddress for loc in sr.locations]
        if address in srLocations:
          yield sr

  def find_all_by_address(self, address: int) -> Generator[BasicResult]:
    """Function is meant to find symbols, functions, defined_data by address. Especially useful for defined_data,
    because the DAT_ symbol name is detached from the data type (defined data). """
    for obj in self.yield_raw_objects():
      ruleId = obj['ruleId']
      if ruleId == 'SYMBOLS':
        sr: SymbolResult = SymbolResult.from_dict(obj) # type: ignore
        srLocations = [loc.physicalLocation.address.absoluteAddress for loc in sr.locations]
        if address in srLocations:
          yield sr
      elif ruleId == "FUNCTIONS":
        fr: FunctionResult = FunctionResult.from_dict(obj)
        frLocations = [loc.physicalLocation.address.absoluteAddress for loc in fr.locations]
        if address in frLocations:
          yield fr
      elif ruleId == "DEFINED_DATA":
        dd: DefinedDataResult = DefinedDataResult.from_dict(obj)
        ddLocations = [loc.physicalLocation.address.absoluteAddress for loc in dd.locations]
        if address in ddLocations:
          yield dd
  
  def namespace_to_location(self, namespace: str):
    return f"/{'/'.join(namespace.split('::'))}"

  def find_all_by_location(self, location: str, recursive: bool = True, lookup_lsymbols: bool = False) -> Generator[BasicResult]:
    looked_up_lsymbols = {}
    for obj in self.yield_raw_objects():
      ruleId = obj['ruleId']
      if ruleId == 'SYMBOLS':
        sr: SymbolResult = SymbolResult.from_dict(obj) # type: ignore
        addresses = [loc.physicalLocation.address.absoluteAddress for loc in dd.locations]
        addresses = [addr for addr in addresses if not addr in looked_up_lsymbols]
        visited = False
        for address in addresses:
          if looked_up_lsymbols[address]:
            visited = True
          looked_up_lsymbols[address] = True
        if not visited:
          if sr.properties.additionalProperties.location == location:
            yield sr
          elif recursive and sr.properties.additionalProperties.location.startswith(location):
            yield sr
      elif ruleId == "FUNCTIONS":
        fr: FunctionResult = FunctionResult.from_dict(obj)
        loc = self.namespace_to_location(fr.properties.additionalProperties.namespace)
        if loc == location:
          yield fr
        elif recursive and loc.startswith(location):
          yield fr
      elif ruleId == "DEFINED_DATA":
        dd: DefinedDataResult = DefinedDataResult.from_dict(obj)
        locations = [
          dd.properties.additionalProperties.location,
          dd.properties.additionalProperties.typeLocation,
          f"{dd.properties.additionalProperties.location}/{dd.properties.additionalProperties.name}",
          f"{dd.properties.additionalProperties.typeLocation}/{dd.properties.additionalProperties.typeName}",
        ]

        for l in locations:
          hit = l == location
          if not hit:
            hit = recursive and l.startswith(location)
          if hit:
            yield dd
            if lookup_lsymbols:
              addresses = [loc.physicalLocation.address.absoluteAddress for loc in dd.locations]
              addresses = [addr for addr in addresses if not addr in looked_up_lsymbols]
              for address in addresses:
                looked_up_lsymbols[address] = True
                yield from self.find_symbols_for_address(address)
