

from typing import Any
from skink.export.location import normalize_location
from skink.sarif.datatypes.AdditionalDataTypeProperties import AdditionalDataTypeProperties
from skink.sarif.datatypes.DataTypeResult import DataTypeResult
from skink.sarif.functions.AdditionalFunctionProperties import AdditionalFunctionProperties
from skink.sarif.functions.FunctionResult import FunctionResult
from skink.sarif.symbols.symbol import SymbolResult


def belongs_in_namespace(result: Any, ns: str):
  prefix = f"{ns}::"
  if isinstance(result, SymbolResult):
    loc = result.properties.additionalProperties.location
    if loc == ns or loc.startswith(prefix):
      return True
  elif isinstance(result, FunctionResult):
    afp: AdditionalFunctionProperties = result.properties.additionalProperties
    if afp.namespace == ns or afp.namespace.startswith(prefix):
      return True
  elif isinstance(result, DataTypeResult):
    adtp: AdditionalDataTypeProperties = result.properties.additionalProperties
    loc = normalize_location(adtp.location) + f"/{adtp.name}"
    nns = loc.replace("/", "::")
    if nns == ns or nns.startswith(prefix):
      return True
  return False # TODO: rough filter