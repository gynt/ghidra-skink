


from dataclasses import dataclass
from typing import Dict
from dataclasses_json import CatchAll, LetterCase, Undefined, dataclass_json
from skink.sarif.TypeInfo import TypeInfo
from skink.sarif.message import Message

@dataclass_json(undefined=Undefined.INCLUDE, letter_case=LetterCase.CAMEL)
@dataclass
class UnionField:
    name: str
    location: str
    field_name: str
    length: int
    ordinal: int
    offset: int
    type: TypeInfo
    extra: CatchAll

@dataclass_json(undefined=Undefined.INCLUDE, letter_case=LetterCase.CAMEL)
@dataclass
class AdditionalUnionProperties:
    name: str
    location: str
    packed: str
    alignment: str
    kind: str
    size: int
    fields: Dict[str, UnionField]
    extra: CatchAll

@dataclass_json(undefined=Undefined.INCLUDE, letter_case=LetterCase.CAMEL)
@dataclass
class UnionProperties:
    additionalProperties: AdditionalUnionProperties
    extra: CatchAll

@dataclass_json(undefined=Undefined.INCLUDE, letter_case=LetterCase.CAMEL)
@dataclass
class UnionResult:
    message: Message
    ruleId: str
    properties: UnionProperties
    extra: CatchAll