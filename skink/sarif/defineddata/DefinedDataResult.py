from typing import List

from skink.sarif.symbols.location import Location
from ..defineddata.DefinedDataProperties import DefinedDataProperties
from ..message import Message

from dataclasses_json import CatchAll, LetterCase, Undefined, dataclass_json


from dataclasses import dataclass


@dataclass_json(undefined=Undefined.INCLUDE, letter_case=LetterCase.CAMEL) # pyright: ignore[reportArgumentType]
@dataclass
class DefinedDataResult:
    message: Message
    ruleId: str
    kind: str
    level: str
    locations: List[Location]
    properties: DefinedDataProperties
    extra: CatchAll