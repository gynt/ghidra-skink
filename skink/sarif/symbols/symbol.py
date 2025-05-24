
from typing import List
from dataclasses_json import CatchAll, LetterCase, Undefined, dataclass_json


from dataclasses import dataclass

from .symbolProperties import SymbolProperties

from .location import Location


@dataclass_json(undefined=Undefined.INCLUDE, letter_case=LetterCase.CAMEL)
@dataclass
class SymbolResult:
    ruleId: str
    kind: str
    level: str
    locations: List[Location]
    properties: SymbolProperties
    extra: CatchAll