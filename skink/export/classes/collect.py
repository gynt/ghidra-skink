import logging
from dataclasses import dataclass, field
from typing import Dict, List, Iterable

from dataclasses_json import dataclass_json
from skink.architecture.functions.function import Function
from skink.architecture.structs.struct import Struct
from skink.architecture.defineddata import DefinedData
from skink.export.location import normalize_location
from skink.sarif import SarifExport
from skink.sarif.BasicResult import BasicResult
from skink.sarif.datatypes.AdditionalDataTypeProperties import AdditionalDataTypeProperties
from skink.sarif.datatypes.DataTypeResult import DataTypeResult
from skink.sarif.functions.AdditionalFunctionProperties import AdditionalFunctionProperties
from skink.sarif.functions.FunctionResult import FunctionResult
from skink.sarif.symbols.symbol import SymbolResult
from skink.sarif.defineddata.DefinedDataResult import DefinedDataResult
from ...architecture.classes.cls import Class, Singleton
from ...architecture.namespaces.namespace import Namespace

@dataclass_json
@dataclass
class PreClass:
  namespace: str
  functions: List[FunctionResult] = field(default_factory=list)
  structure: DataTypeResult = None
  singleton: DefinedDataResult = None
  singleton_symbol: SymbolResult = None


def collect_classes(results: Iterable[BasicResult]):
  symbol_db: Dict[int, List[SymbolResult]] = {}
  ddr_db: Dict[int, DefinedDataResult] = {}
  classes: Dict[str, PreClass] = {}
  for result in results:
    if isinstance(result, SymbolResult):
      sr: SymbolResult = result
      for l in sr.locations:
        addr = l.physicalLocation.address.absoluteAddress
        if not addr in symbol_db:
          symbol_db[addr] = []
        symbol_db[addr].append(sr)
    elif isinstance(result, DefinedDataResult):
      ddr: DefinedDataResult = result
      for l in ddr.locations:
        addr = l.physicalLocation.address.absoluteAddress
        if addr in ddr_db:
          logging.log(logging.DEBUG, f"skipping duplicate: {hex(addr)}")
          continue
        ddr_db[addr] = ddr
    elif isinstance(result, FunctionResult):
      ap: AdditionalFunctionProperties = result.properties.additionalProperties
      if ap.namespaceIsClass:
        ns = ap.namespace
        if not ns in classes:
          classes[ns] = PreClass(ns)
        classes[ns].functions.append(result)
    elif isinstance(result, DataTypeResult):
      ap: AdditionalDataTypeProperties = result.properties.additionalProperties
      loc = normalize_location(ap.location) + f"/{ap.name}"
      ns = loc.replace("/", "::")
      if not ns in classes:
        classes[ns] = PreClass(ns)
      if classes[ns].structure:
        if classes[ns].structure != result:
          raise Exception(f"structure already set and different: {ns}")
      # TODO: is this dirty? We promote this struct to a class struct and therefore move it next to the cls file
      # cp = DataTypeResult.from_dict(result.to_dict())
      # cp.properties.additionalProperties.location = loc
      classes[ns].structure = result
  for ns, preclass in classes.items():
    if not preclass.functions:
      continue
    functions = [Function(fr) for fr in preclass.functions]
    struct = None
    single = None
    if preclass.structure:
      struct = Struct(preclass.structure)
      for addr, ssr in ddr_db.items():
        ssr_loc = ssr.properties.additionalProperties.location
        ssr_name = ssr.properties.additionalProperties.name
        if ssr_loc == struct.s.properties.additionalProperties.location:
          if ssr_name == struct.s.properties.additionalProperties.name:  
            if addr in symbol_db:
              sr = symbol_db[addr][0] # TODO: improve
              single = Singleton(defined_data = DefinedData(ssr), sr = sr)
       
    yield Class(namespace=ns, functions=functions, structure=struct, singleton=single)
  
def collect_classes_from_export(se: SarifExport):
  return collect_classes(se.runs[0].results)


@dataclass
class PreNamespace:
  namespace: str
  functions: List[FunctionResult] = field(default_factory=list)

def collect_namespaced_functions(results):
  namespaces: Dict[str, PreNamespace] = {}
  for result in results:
    if isinstance(result, FunctionResult):
      ap: AdditionalFunctionProperties = result.properties.additionalProperties
      if not ap.namespaceIsClass:
        ns = ap.namespace
        if not ns in namespaces:
          namespaces[ns] = PreNamespace(ns)
        namespaces[ns].functions.append(result)
  for ns, prenamespace in namespaces.items():
    if not prenamespace.functions:
      continue
    functions = [Function(fr) for fr in prenamespace.functions]
    yield Namespace(namespace=ns, functions=functions)