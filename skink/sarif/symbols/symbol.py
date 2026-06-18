
from typing import List
from dataclasses_json import CatchAll, LetterCase, Undefined, dataclass_json


from dataclasses import dataclass

from .symbolProperties import SymbolProperties

from .location import Location

from ..message import Message


@dataclass_json(undefined=Undefined.INCLUDE, letter_case=LetterCase.CAMEL) # pyright: ignore[reportArgumentType]
@dataclass
class SymbolResult:
    message: Message
    ruleId: str
    kind: str
    level: str
    locations: List[Location]
    properties: SymbolProperties
    extra: CatchAll