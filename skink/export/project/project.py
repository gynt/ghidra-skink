from dataclasses import dataclass
from typing import Any, Generator, Iterable, List, Set
import ijson, json

from skink.sarif.BasicResult import BasicResult
from skink.sarif.decode_results import DECODE_RESULT_STATE, decode_result

from ..project.databases.symboldatabase import SymbolDatabase
from ...sarif.symbols.symbol import SymbolResult
from ...sarif.functions.FunctionResult import FunctionResult
from ...sarif.datatypes.DataTypeResult import DataTypeResult
from ...sarif.defineddata.DefinedDataResult import DefinedDataResult
from ...sarif.datatypes.EnumResult import EnumResult
from ...sarif.datatypes.UnionResult import UnionResult
from ...sarif.datatypes.FunctionSignatureResult import FunctionSignatureResult
from skink.sarif.datatypes.TypedefResult import TypedefResult

import pathlib
import pickle

from ...logger import log, logging

def log_ijson_backend():
  log(logging.DEBUG, f"ijson: using backend {ijson.backend_name}")

def promote_pathstring(path: str | pathlib.Path):
  if isinstance(path, pathlib.Path):
    return path
  return pathlib.Path(path).absolute()

@dataclass
class SingletonSearchResult:
  dtr: DataTypeResult
  ddr: DefinedDataResult
  sr: SymbolResult

class Project(object):
  
  def __init__(self, 
               path: pathlib.Path | str | None = None, 
               paths: Iterable[str] | Iterable[pathlib.Path] | None = None, 
               raw_objects: Iterable[Any] | None = None,
               objects: Iterable[Any] | None = None,
               cache_objects: bool = False,
               cache_symbols_to_path: str | None = None):
    self.paths: List[pathlib.Path] = list()
    self.raw_objects = None
    self.objects = None
    if path:
      self.paths = [promote_pathstring(path)]
    elif paths:
      self.paths = list(promote_pathstring(p) for p in paths)
    elif raw_objects:
      self.raw_objects = raw_objects
    elif objects:
      self.objects = objects
    else:
      raise Exception()
    self.symdb = SymbolDatabase()
    self.cache_symbols_to_path = cache_symbols_to_path
    if self.cache_symbols_to_path:
      if pathlib.Path(self.cache_symbols_to_path).exists():
        with open(self.cache_symbols_to_path, 'rb') as f:
          self.symdb = pickle.load(file=f)
    self.counts = {'total': 0, 'member': 0, 'class': 0, 'namespace': 0, 'unknown': 0}
    self.cache_objects = cache_objects
    

  def save_project(self, path: str | pathlib.Path):
    items = list(obj for obj in self.yield_raw_objects())
    pathlib.Path(path).write_text(json.dumps({
      "runs": [{
        "results": items
      }]
    }))

  @staticmethod
  def load_saved_project(path: str | pathlib.Path):
    return Project(path = path)
  
  def merge_project(self, other: "Project"):
    if self.paths and other.paths:
      return Project(paths = self.paths + other.paths)
    if self.objects and other.objects:
      return Project(objects = self.objects + other.objects)
    if self.raw_objects and other.raw_objects:
      return Project(raw_objects = self.raw_objects + other.raw_objects)
    return Project(raw_objects=list(self.yield_raw_objects()) + list(other.yield_raw_objects()))

  def reset_counts(self):
    self.counts = {'total': 0, 'member': 0, 'class': 0, 'namespace': 0, 'unknown': 0}    

  def yield_raw_objects(self) -> Generator[Any]:
    if self.raw_objects:
      yield from self.raw_objects
    elif self.objects:
      logging.log(logging.WARNING, "rawify-ing parsed objects to raw objects, probably not what you want")
      for obj in self.yield_objects():
        yield obj.to_dict() # rawify
    else:
      if self.cache_objects:
        if not self.raw_objects:
          self.raw_objects = []
        for path in self.paths:
          with open(path, 'r') as f:
            for item in ijson.items(f, 'runs.item.results.item'):
              self.raw_objects.append(item)
        yield from self.raw_objects
      else:
        for path in self.paths:
          with open(path, 'r') as f:
            yield from ijson.items(f, 'runs.item.results.item')

  def yield_objects(self, debug=False) -> Generator[BasicResult]:
    if self.objects:
      yield from self.objects
    else:
      with DECODE_RESULT_STATE as s:
        if self.cache_objects:
          if not self.objects:
            self.objects = []
          for obj in self.yield_raw_objects():
            dobj = decode_result(obj)
            self.objects.append(dobj)
          yield from self.objects
        else:
          for obj in self.yield_raw_objects():
            if debug:
              log(logging.DEBUG, obj)
            yield decode_result(obj)

  # def find_first_defined_data_for_class(self, dtr: DataTypeResult):
  #   loc = dtr.properties.additionalProperties.location
  #   name = dtr.properties.additionalProperties.name
  #   for obj in self.yield_objects():
  #     if obj.ruleId == "DEFINED_DATA":
  #       ddr: DefinedDataResult = obj
  #       if ddr.properties.additionalProperties.location == loc:
  #         if ddr.properties.additionalProperties.name == name:
  #           if len(ddr.locations) == 1:
  #             address = ddr.locations[0].physicalLocation.address.absoluteAddress
  #             for obj2 in self.yield_objects():
  #               if obj2.ruleId == "SYMBOL":
  #                 sr: SymbolResult = obj2
  #                 if len(sr.locations) == 1:
  #                   if sr.locations[0].physicalLocation.address.absoluteAddress == address:
  #                     return SingletonSearchResult(dtr, ddr, sr)

  def process_symbol_results(self, yield_filters = ['address'], prefix = "", permit_overwrite = False, drop_submembers = True, store_symbol_result = False) -> Generator[SymbolResult]:
    if not self.paths:
      raise Exception(f"no paths set: {self.paths}")
    
    self.reset_counts()
    
    for obj in self.yield_raw_objects():
      if obj['ruleId'] == 'SYMBOLS':
        sr: SymbolResult = SymbolResult.from_dict(obj) # type: ignore
#         log(logging.DEBUG, sr)
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

  def process_all_symbol_results(self, log_progress=0, clear_cache=False, *args, **kwargs):
    if not clear_cache and (self.cache_symbols_to_path and pathlib.Path(self.cache_symbols_to_path).exists()):
      log(logging.INFO, f"using cached symbols: {self.cache_symbols_to_path}")
      return
    progress_i = 0
    for _ in self.process_symbol_results(*args, **kwargs):
      progress_i += 1
      if log_progress:
        if progress_i % log_progress == 0:
          logging.log(logging.DEBUG, f"progress:\t{progress_i}")
      continue
    if self.cache_symbols_to_path:
      logging.log(logging.INFO, f"caching symbols to: {self.cache_symbols_to_path}")
      with open(self.cache_symbols_to_path, 'wb') as f:
        pickle.dump(obj=self.symdb, file=f)

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

  def find_all_by_location(self, location: str, name: str = None, recursive: bool = False, lookup_lsymbols: bool = False) -> Generator[BasicResult]:
    looked_up_lsymbols = {}

    def find_symbols(addresses):
      addresses = [addr for addr in addresses if not addr in looked_up_lsymbols]
      for address in addresses:
        looked_up_lsymbols[address] = True
        # TODO: avoid another iteration over the same file...
        for entry in self.symdb.by_address(address=address, except_on_missing=False):
          yield entry.extra

    for obj in self.yield_raw_objects():
      try:
        ruleId = obj['ruleId']
        if ruleId == 'SYMBOLS':
          sr: SymbolResult = SymbolResult.from_dict(obj) # type: ignore
          addresses = [loc.physicalLocation.address.absoluteAddress for loc in dd.locations]
          addresses = [addr for addr in addresses if not addr in looked_up_lsymbols]
          visited = False
          for address in addresses:
            if address in looked_up_lsymbols and looked_up_lsymbols[address]:
              visited = True
            looked_up_lsymbols[address] = True
          if not visited:
            if sr.properties.additionalProperties.location == location:
              if name:
                if sr.properties.additionalProperties.name == name:
                  yield sr
              else:
                yield sr
            elif recursive and sr.properties.additionalProperties.location.startswith(location):
              yield sr
        elif ruleId == "FUNCTIONS":
          fr: FunctionResult = FunctionResult.from_dict(obj)
          loc = self.namespace_to_location(fr.properties.additionalProperties.namespace)
          if loc == location:
            if name:
              if fr.properties.additionalProperties.name == name:
                yield fr
            else:
              yield fr
          elif recursive and loc.startswith(location):
            yield fr
        elif ruleId == "DATATYPE":
          if obj["message"]["text"] == "DT.Struct":
            dtr: DataTypeResult = DataTypeResult.from_dict(obj)
            locations: List[str] = [
              dtr.properties.additionalProperties.location,
              f"{dtr.properties.additionalProperties.location}/{dtr.properties.additionalProperties.name}",
            ]
            for l in locations:
              hit = l == location
              if not hit:
                hit = recursive and l.startswith(location)
              else:
                if name:
                  if dtr.properties.additionalProperties.name == name:
                    yield dtr
                else:
                  yield dtr
                continue
              if hit:
                yield dtr
          elif obj["message"]["text"] == "DT.Enum":
            dtr: EnumResult = EnumResult.from_dict(obj)
            locations: List[str] = [
              dtr.properties.additionalProperties.location,
              f"{dtr.properties.additionalProperties.location}/{dtr.properties.additionalProperties.name}",
            ]
            for l in locations:
              hit = l == location
              if not hit:
                hit = recursive and l.startswith(location)
              else:
                if name:
                  if dtr.properties.additionalProperties.name == name:
                    yield dtr
                else:
                  yield dtr
                continue
              if hit:
                yield dtr
          elif obj["message"]["text"] == "DT.Union":
            dtr: UnionResult = UnionResult.from_dict(obj)
            locations: List[str] = [
              dtr.properties.additionalProperties.location,
              f"{dtr.properties.additionalProperties.location}/{dtr.properties.additionalProperties.name}",
            ]
            for l in locations:
              hit = l == location
              if not hit:
                hit = recursive and l.startswith(location)
              else:
                if name:
                  if dtr.properties.additionalProperties.name == name:
                    yield dtr
                else:
                  yield dtr
                continue
              if hit:
                yield dtr
          elif obj["message"]["text"] == "DT.Function":
            dtr: FunctionSignatureResult = FunctionSignatureResult.from_dict(obj)
            locations: List[str] = [
              dtr.properties.additionalProperties.location,
              f"{dtr.properties.additionalProperties.location}/{dtr.properties.additionalProperties.name}",
            ]
            for l in locations:
              hit = l == location
              if not hit:
                hit = recursive and l.startswith(location)
              else:
                if name:
                  if dtr.properties.additionalProperties.name == name:
                    yield dtr
                else:
                  yield dtr
                continue
              if hit:
                yield dtr
          elif obj["message"]["text"] == "DT.Typedef":
            dtr: TypedefResult = TypedefResult.from_dict(obj)
            locations: List[str] = [
              dtr.properties.additionalProperties.location,
              f"{dtr.properties.additionalProperties.location}/{dtr.properties.additionalProperties.name}",
            ]
            for l in locations:
              hit = l == location
              if not hit:
                hit = recursive and l.startswith(location)
              else:
                if name:
                  if dtr.properties.additionalProperties.name == name:
                    yield dtr
                else:
                  yield dtr
                continue
              if hit:
                yield dtr
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
            else:
              if name:
                if dd.properties.additionalProperties.name == name:
                  yield dd
                  if lookup_lsymbols:
                    yield from find_symbols(addresses=[loc.physicalLocation.address.absoluteAddress for loc in dd.locations])
              else:
                yield dd
                if lookup_lsymbols:
                  yield from find_symbols(addresses=[loc.physicalLocation.address.absoluteAddress for loc in dd.locations])
              continue
            if hit:
              yield dd
              if lookup_lsymbols:
                yield from find_symbols(addresses=[loc.physicalLocation.address.absoluteAddress for loc in dd.locations])
      except Exception as e:
        log(logging.ERROR, obj)
        raise(e)
