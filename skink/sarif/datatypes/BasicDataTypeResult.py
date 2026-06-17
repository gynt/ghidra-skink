from skink.sarif.message import Message
from .DataTypeProperties import DataTypeProperties


from dataclasses_json import CatchAll, LetterCase, Undefined, dataclass_json


from dataclasses import dataclass

@dataclass_json(undefined=Undefined.INCLUDE, letter_case=LetterCase.CAMEL) # pyright: ignore[reportArgumentType]
@dataclass
class BasicAdditionalDataTypeProperties:
    extra: CatchAll
    name: str = ""
    location: str = ""
    

@dataclass_json(undefined=Undefined.INCLUDE, letter_case=LetterCase.CAMEL) # pyright: ignore[reportArgumentType]
@dataclass
class BasicDataTypeProperties:
    additionalProperties: BasicAdditionalDataTypeProperties
    extra: CatchAll

@dataclass_json(undefined=Undefined.INCLUDE, letter_case=LetterCase.CAMEL) # pyright: ignore[reportArgumentType]
@dataclass
class BasicDataTypeResult:
    message: Message
    ruleId: str
    properties: BasicDataTypeProperties
    extra: CatchAll