from typing import Dict
from skink.sarif.TypeInfo import TypeInfo
from skink.sarif.message import Message
from .DataTypeProperties import DataTypeProperties


from dataclasses_json import CatchAll, LetterCase, Undefined, dataclass_json


from dataclasses import dataclass

@dataclass_json(undefined=Undefined.INCLUDE, letter_case=LetterCase.CAMEL)
@dataclass
class AdditionalTypedefProperties:
    type: TypeInfo
    kind: str
    size: int
    name: str
    location: str
    extra: CatchAll
    endian: str = ""
    typeName: str = ""
    typeLocation: str = ""

@dataclass_json(undefined=Undefined.INCLUDE, letter_case=LetterCase.CAMEL)
@dataclass
class TypedefProperties:
    additionalProperties: AdditionalTypedefProperties
    extra: CatchAll

@dataclass_json(undefined=Undefined.INCLUDE, letter_case=LetterCase.CAMEL)
@dataclass
class TypedefResult:
    message: Message
    ruleId: str
    properties: TypedefProperties
    extra: CatchAll