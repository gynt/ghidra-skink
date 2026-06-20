from dataclasses import dataclass
from typing import Any, Dict, Generator, Iterable, List, Set
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
from skink.sarif.datatypes.TypedObject import TypedObjectResult
from skink.sarif.datatypes.BasicDataTypeResult import BasicDataTypeResult
from skink.export.project.databaseplan import DatabasePlan, SymbolsDatabasePlan, DatatypeDatabasePlan, DefineddataDatabasePlan, FunctionDatabasePlan

from skink.export.util import *

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
               cache_path: str | None = None):
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
    self.db_sym = SymbolDatabase()
    self.db_meta: Dict[str, SymbolResult] = {}
    self.db_defineddata: Dict[int, DefinedDataResult] = {}
    self.db_datatype: Dict[str, BasicDataTypeResult] = {}
    self.db_function: Dict[str | int, FunctionResult] = {}
    self.cache_path: pathlib.Path = pathlib.Path(cache_path)
    self.counts = {'total': 0, 'member': 0, 'class': 0, 'namespace': 0, 'unknown': 0}
    self.cache_raw_objects = cache_objects

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
      raise Exception("rawify-ing parsed objects to raw objects, probably not what you want")
      for obj in self.yield_objects():
        # Make raw again...
        yield obj.to_dict() # type: ignore
    else:
      if self.cache_raw_objects:
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
        if self.cache_raw_objects:
          if not self.objects:
            self.objects = []
          elif isinstance(self.objects, Iterable):
            self.objects = list(self.objects)
          for obj in self.yield_raw_objects():
            dobj = decode_result(obj)
            self.objects.append(dobj)
          yield from self.objects
        else:
          for obj in self.yield_raw_objects():
            if debug:
              log(logging.DEBUG, obj)
            yield decode_result(obj)

  def _build_database_symbols_meta(self, obj, plan: DatabasePlan):
    sr: SymbolResult = SymbolResult.from_dict(obj) # type: ignore
    if not plan.filter(sr):
      return
    n = sr.properties.additionalProperties.name
    l = sr.properties.additionalProperties.location
    a = sr.locations[0].physicalLocation.address.absoluteAddress
    if a == 0:
      if not l:
        self.db_meta[f"{n}"] = sr
      else:
        self.db_meta[f"{l}{n}"] = sr

  def _build_database_symbols(self, obj, plan: SymbolsDatabasePlan):
    prefix = plan.prefix
    drop_submembers = plan.drop_submembers
    permit_overwrite = plan.permit_overwrite
    store_symbol_result = plan.store_symbol_result
    include_zero_address = plan.include_zero_address

    sr: SymbolResult = SymbolResult.from_dict(obj) # type: ignore
    if not plan.filter(sr):
      return
#         log(logging.DEBUG, sr)
    n = sr.properties.additionalProperties.name
    l = sr.properties.additionalProperties.location
    if prefix:
      if not l.startswith(f"{prefix}::"):
        if l != '' or n != prefix:
          return
    a = sr.locations[0].physicalLocation.address.absoluteAddress
    addrs = [loc.physicalLocation.address.absoluteAddress for loc in sr.locations]
    if all(addr == 0 for addr in addrs) and not include_zero_address:
      return
    e = sr.properties.additionalProperties.kind == 'external'
    k = sr.properties.additionalProperties.type
    if not k and sr.properties.additionalProperties.namespaceIsClass:
      k = 'member'
    elif not k:
      sp = l[:-2] # remove trailing "::"
      if sp and self.db_sym.has(sp):
        if self.db_sym.get(sp).kind == "namespace":
          k = 'member'
    
    if drop_submembers:
      sp = l[:-2]
      if sp and self.db_sym.has(sp):
        if self.db_sym.get(sp).kind == 'member':
          return
    
    if self.db_sym.add_entry(path=f"{l}{n}", 
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

  def _build_database_datatype(self, obj, plan: DatatypeDatabasePlan):
    subtype = obj['message']['text']
    if subtype in self.DATATYPE_MAPPING:
      x: BasicDataTypeResult = self.DATATYPE_MAPPING[subtype].from_dict(obj)

      if not plan.filter(x):
        return
      loc = x.properties.additionalProperties.location
      name = x.properties.additionalProperties.name
      full_loc = loc_name_to_location(loc, name)
      assert full_loc[0] == "/"
      self.db_datatype[full_loc] = x
      rewritten_loc = plan.location_rewriter(full_loc)
      if rewritten_loc != full_loc:
        self.db_datatype[rewritten_loc] = x

  def _build_database_defineddata(self, obj, plan: DefineddataDatabasePlan):
    ddr: DefinedDataResult = DefinedDataResult.from_dict(obj) # type: ignore
    if not plan.filter(ddr):
      return
    for l in ddr.locations:
      absolute_address = l.physicalLocation.address.absoluteAddress
      if absolute_address:
        self.db_defineddata[absolute_address] = ddr

  def _build_database_function(self, obj, plan: DatabasePlan):
    fr : FunctionResult = FunctionResult.from_dict(obj)
    if not plan.filter(fr):
      return
    ns_parts = [n for n in [fr.properties.additionalProperties.namespace, fr.properties.additionalProperties.name] if n]
    ns = f"{'::'.join(ns_parts)}"
    loc = f"/{ns.replace('::', '/')}"
    self.db_function[loc] = fr
    self.db_function[ns] = fr
    for loc in fr.locations:
      addr = loc.physicalLocation.address.absoluteAddress
      if addr:
        self.db_function[addr] = fr

  def build_database(self,
                     plan_symbols: SymbolsDatabasePlan = None,
                     plan_defineddata: DefineddataDatabasePlan = None,
                     plan_datatype: DatatypeDatabasePlan = None,
                     plan_function: FunctionDatabasePlan = None,
                     log_progress=0, clear_cache=False):
    if clear_cache and self.cache_path:
      (self.cache_path / 'db_sym.bin').unlink(missing_ok=True)
      (self.cache_path / 'db_defineddata.bin').unlink(missing_ok=True)
      (self.cache_path / 'db_datatype.bin').unlink(missing_ok=True)
      (self.cache_path / 'db_function.bin').unlink(missing_ok=True)
      (self.cache_path / 'db_meta.bin').unlink(missing_ok=True)
    if self.cache_path and pathlib.Path(self.cache_path).exists():
      log(logging.INFO, f"using cached symbols: {self.cache_path}")
      if (self.cache_path / 'db_sym.bin').exists():
        with (self.cache_path / 'db_sym.bin').open('rb') as f:
          self.db_sym = pickle.load(file=f)
        with (self.cache_path / 'db_defineddata.bin').open('rb') as f:
          self.db_defineddata = pickle.load(file=f)
        with (self.cache_path / 'db_datatype.bin').open('rb') as f:
          self.db_datatype = pickle.load(file=f)
        with (self.cache_path / 'db_function.bin').open('rb') as f:
          self.db_function = pickle.load(file=f)
        with (self.cache_path / 'db_meta.bin').open('rb') as f:
          self.db_meta = pickle.load(file=f)
        return
    log(logging.INFO, f"building database, caching in: {self.cache_path}")
    progress_i = 0
    self.reset_counts()
    plan_ruleId_index: Dict[str, DatabasePlan] = {plan.ruleId: plan for plan in [plan_symbols,
                                                                                 plan_defineddata,
                                                                                 plan_datatype,
                                                                                 plan_function] if plan}
    ruleIds = plan_ruleId_index.keys()
    for obj in self.yield_raw_objects():
      progress_i += 1
      if log_progress:
        if progress_i % log_progress == 0:
          logging.log(logging.DEBUG, f"progress:\t{progress_i}")

      ruleId = obj['ruleId']
      if ruleId not in ruleIds:
        continue
      
      if ruleId == "SYMBOLS":
        self._build_database_symbols(obj, plan_symbols)
        if plan_symbols.meta:
          self._build_database_symbols_meta(obj, plan_symbols.meta)
      elif ruleId == "DATATYPE":
        self._build_database_datatype(obj, plan_datatype)
      elif ruleId == "DEFINED_DATA":
        self._build_database_defineddata(obj, plan_defineddata)
      elif ruleId == "FUNCTIONS":
        self._build_database_function(obj, plan_function)
    if self.cache_path:
      self.cache_path.mkdir(parents=True, exist_ok=True)
      logging.log(logging.INFO, f"caching symbols to: {self.cache_path}")
      with (self.cache_path / 'db_sym.bin').open('wb') as f:
        pickle.dump(obj=self.db_sym, file=f)
      with (self.cache_path / 'db_defineddata.bin').open('wb') as f:
        pickle.dump(obj=self.db_defineddata, file=f)
      with (self.cache_path / 'db_datatype.bin').open('wb') as f:
        pickle.dump(obj=self.db_datatype, file=f)
      with (self.cache_path / 'db_function.bin').open('wb') as f:
        pickle.dump(obj=self.db_function, file=f)
      with (self.cache_path / 'db_meta.bin').open('wb') as f:
        pickle.dump(obj=self.db_meta, file=f)

  # Used
  def find_global_primary_symbol_defined_data_pairs_by_address(self):
    raw_symbols_by_address: Dict[int, List[str]] = {}
    raw_defined_datas_by_address: Dict[int, List[DefinedDataResult]] = {}
    for addr, entries in self.db_sym.address_db.items():
      for entry in entries:
        symbol = entry.extra
        kind = symbol.properties.additionalProperties.kind
        primary = symbol.properties.additionalProperties.primary
        if not primary or kind != "global":
          continue
        if addr > 0:
          if addr not in raw_symbols_by_address:
            raw_symbols_by_address[addr] = []
          l = raw_symbols_by_address[addr]
          s = symbol.properties.additionalProperties.name
          if not s in l:  
            l.append(s)
    for addr, dd in self.db_defineddata.items():
      if addr > 0:
        if addr not in raw_defined_datas_by_address:
          raw_defined_datas_by_address[addr] = []
        l = raw_defined_datas_by_address[addr]
        if not dd in l:
          l.append(dd)
    for address, dd_list in raw_defined_datas_by_address.items():
      if not dd_list:
        continue
      if not address in raw_symbols_by_address:
        # come up with a ghidra-compatible symbol
        dd = dd_list[0]
        tn = dd.properties.additionalProperties.typeName
        s_addr_part = f"{address:0{8}x}"
        prefix = "DAT_"
        if tn.lower().startswith("undefined"):
          pass
        elif tn.lower().startswith("float"):
          prefix = "FLOAT_"
        elif tn.lower().startswith("double"):
          prefix = "DOUBLE_"
        elif tn.lower().startswith("int"):
          prefix = "INT_"
        elif tn.lower().startswith("short"):
          prefix = "SHORT_"
        elif tn.lower().startswith("byte"):
          prefix = "BYTE_"
        elif tn.lower().startswith("dword"):
          prefix = "DWORD_"
        elif tn.lower().startswith("boolenum"):
          prefix = "BOOLEnum_"
        elif tn.lower().startswith("bool"):
          prefix = "BOOL_"
        elif tn.lower().startswith("char"):
          prefix = "CHAR_"
        elif tn.lower().startswith("string"):
          prefix = "CHAR_" # doesn't actually appear often in decompiled output...
        elif tn.lower().startswith("pointer"):
          prefix = "PTR_"
        if "[" in tn:
          prefix = prefix + "ARRAY_"
        sym = f"{prefix}{s_addr_part}"
        raw_symbols_by_address[address] = [sym]
    for address, symbol_list in raw_symbols_by_address.items():
      if not address in raw_defined_datas_by_address:
        # undefined data is uncompilable...
        continue
      isClass = False
      rdd_list = raw_defined_datas_by_address[address]
      dd = rdd_list[0]
      sym = symbol_list[0]
      dd_typename = dd.properties.additionalProperties.typeName
      dd_loc = loc_name_to_location(dd.properties.additionalProperties.typeLocation, dd_typename)
      dt = self.db_datatype[dd_loc] if dd_loc in self.db_datatype else None
      if not dt:
        if dd_typename.endswith("]"):
          ob = dd_typename.find("[")
          dd_typename_root = dd_typename[:ob]
          dd_loc = loc_name_to_location(dd.properties.additionalProperties.typeLocation, dd_typename_root)
          dt = self.db_datatype[dd_loc] if dd_loc in self.db_datatype else None
      if not dt:
        if dd_loc.startswith("/_HoldStrong"):
          logging.log(logging.WARN, f"could not find DataTypeResult for: {dd_loc}")
          dd_loc = loc_name_to_location(dd.properties.additionalProperties.typeLocation, dd.properties.additionalProperties.typeName)
      if isinstance(dt, TypedObjectResult):
        tor: TypedObjectResult = dt
        if tor.properties.additionalProperties.kind == "pointer":
          tor_name = tor.properties.additionalProperties.type.name
          tor_loc = tor.properties.additionalProperties.type.location
          tor_dt_loc = loc_name_to_location(tor_loc, tor_name)
          dt = self.db_datatype[tor_dt_loc] if tor_dt_loc in self.db_datatype else None
          dd_loc = loc_name_to_location(tor_loc, tor_name)
          if dt:
            logging.log(logging.INFO, f"found pointer DataTypeResult for: {dd_loc}")

      ns = location_to_namespace(dd_loc)
      
      if ns in self.db_meta:
        isClass = self.db_meta[ns].properties.additionalProperties.type == "class"
      yield address, sym, dd, dt, isClass

  def find_all_by_location(self, location: str, name: str = None, recursive: bool = False, lookup_lsymbols: bool = False) -> Generator[BasicResult]:
    if location[0] != "/":
      raise Exception("location should start with '/'")
    
    target = location
    if name:
      target = f"{location}/{name}"
    target_namespace = location_to_namespace(target)
    
    for key, value in self.db_datatype.items():
      if recursive and key.startswith(target):
        yield value
      elif key == target:
        yield value

    for key, value in self.db_meta.items():
      if recursive and key.startswith(target_namespace):
        yield value
      elif key == target_namespace:
        yield value

    for key, value in self.db_sym.db.items():
      if recursive and key.startswith(target_namespace):
        yield value.extra
      elif key == target_namespace:
        yield value.extra

    for key, value in self.db_function.items():
      if isinstance(key, str):
        if recursive and key.startswith(target_namespace):
          yield value
        elif key == target_namespace:
          yield value

    for addr, value in self.db_defineddata.items():
      locations = [
        value.properties.additionalProperties.location,
        value.properties.additionalProperties.typeLocation,
        f"{value.properties.additionalProperties.location}/{value.properties.additionalProperties.name}",
        f"{value.properties.additionalProperties.typeLocation}/{value.properties.additionalProperties.typeName}",
      ]
      hit = False
      for loc in locations:
        if recursive and loc.startswith(target):
          hit = True
          yield value
        elif loc == target:
          hit = True
          yield value
    
      if lookup_lsymbols:
        if hit:
          addresses = [loc.physicalLocation.address.absoluteAddress for loc in value.locations]
          for addr in addresses:
            if addr in self.db_sym.address_db:
              for entry in self.db_sym.address_db[addr]:
                yield entry.extra

  DATATYPE_MAPPING = {"DT.Struct": DataTypeResult,
                      "DT.Enum": EnumResult,
                      "DT.Union": UnionResult,
                      "DT.Function": FunctionSignatureResult,
                      "DT.Typedef": TypedefResult,
                      "DT.TypedObject": TypedObjectResult}

  def find_all_by_location__deprecated(self, location: str, name: str = None, recursive: bool = False, lookup_lsymbols: bool = False) -> Generator[BasicResult]:
    looked_up_lsymbols = {}

    def find_symbols(addresses):
      addresses = [addr for addr in addresses if not addr in looked_up_lsymbols]
      for address in addresses:
        looked_up_lsymbols[address] = True
        # TODO: avoid another iteration over the same file...
        for entry in self.db_sym.by_address(address=address, except_on_missing=False):
          yield entry.extra

    for obj in self.yield_raw_objects():
      try:
        ruleId = obj['ruleId']
        if ruleId == 'SYMBOLS':
          sr: SymbolResult = SymbolResult.from_dict(obj) # type: ignore
          addresses = [loc.physicalLocation.address.absoluteAddress for loc in sr.locations]
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
          fr: FunctionResult = FunctionResult.from_dict(obj) # type: ignore
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
          subtype = obj["message"]["text"]
          if subtype in self.DATATYPE_MAPPING:
            dtr: BasicDataTypeResult = self.DATATYPE_MAPPING[subtype].from_dict(obj)
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
          dd: DefinedDataResult = DefinedDataResult.from_dict(obj) # type: ignore
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
