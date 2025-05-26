


from dataclasses import dataclass
from typing import Dict
from dataclasses_json import CatchAll, LetterCase, Undefined, dataclass_json
from skink.sarif.message import Message

@dataclass_json(undefined=Undefined.INCLUDE, letter_case=LetterCase.CAMEL)
@dataclass
class AdditionalEnumProperties:
    size: int
    base: str
    constants: Dict[str, int]
    name: str
    location: str
    extra: CatchAll

@dataclass_json(undefined=Undefined.INCLUDE, letter_case=LetterCase.CAMEL)
@dataclass
class EnumProperties:
    additionalProperties: AdditionalEnumProperties
    extra: CatchAll

@dataclass_json(undefined=Undefined.INCLUDE, letter_case=LetterCase.CAMEL)
@dataclass
class EnumResult:
    message: Message
    ruleId: str
    properties: EnumProperties
    extra: CatchAll