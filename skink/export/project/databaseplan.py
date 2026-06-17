from dataclasses import dataclass, field
from collections.abc import Callable

from skink.sarif.BasicResult import BasicResult

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
  
  def __post_init__(self):
      object.__setattr__(self, 'ruleId', "SYMBOLS")
