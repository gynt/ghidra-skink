from typing import List

from skink.sarif.symbols.location import Location

from .FunctionProperties import FunctionProperties


from dataclasses_json import CatchAll, LetterCase, Undefined, dataclass_json


from dataclasses import dataclass


@dataclass_json(undefined=Undefined.INCLUDE, letter_case=LetterCase.CAMEL) # pyright: ignore[reportArgumentType]
@dataclass
class FunctionResult:
    ruleId: str
    locations: List[Location]
    properties: FunctionProperties
    extra: CatchAll