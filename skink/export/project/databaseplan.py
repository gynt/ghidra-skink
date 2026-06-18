from dataclasses import dataclass, field
from collections.abc import Callable

from skink.sarif.BasicResult import BasicResult
from skink.sarif.defineddata.DefinedDataResult import DefinedDataResult
from skink.sarif.symbols.symbol import SymbolResult
from skink.sarif.datatypes.DataTypeResult import DataTypeResult
from skink.sarif.functions.FunctionResult import FunctionResult

@dataclass
class DatabasePlan:
  ruleId: str = field(default="", kw_only=True)
  filter: Callable[[BasicResult], bool] = lambda _: True
   
@dataclass
class SymbolsDatabasePlan(DatabasePlan):
  prefix: str = ""
  permit_overwrite: bool = False
  drop_submembers: bool = True
  store_symbol_result: bool = False
  filter: Callable[[SymbolResult], bool] = lambda _: True
  include_zero_address: bool = False
  meta: DatabasePlan = field(default_factory=DatabasePlan)
  
  def __post_init__(self):
      object.__setattr__(self, 'ruleId', "SYMBOLS")

@dataclass
class DatatypeDatabasePlan(DatabasePlan):
  location_rewriter: Callable[[str], str] = lambda x: x
  filter: Callable[[DataTypeResult], bool] = lambda _: True
  
  def __post_init__(self):
      object.__setattr__(self, 'ruleId', "DATATYPE")

@dataclass
class DefineddataDatabasePlan(DatabasePlan):
  filter: Callable[[DefinedDataResult], bool] = lambda _: True

  def __post_init__(self):
      object.__setattr__(self, 'ruleId', "DEFINED_DATA")

@dataclass
class FunctionDatabasePlan(DatabasePlan):
  filter: Callable[[FunctionResult], bool] = lambda _: True

  def __post_init__(self):
      object.__setattr__(self, 'ruleId', "FUNCTIONS")