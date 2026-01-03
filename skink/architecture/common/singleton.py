from dataclasses import dataclass

from skink.architecture.defineddata import DefinedData
from skink.sarif.symbols.symbol import SymbolResult


@dataclass
class Singleton:
  defined_data: DefinedData
  sr: SymbolResult