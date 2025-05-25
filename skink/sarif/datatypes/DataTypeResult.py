from skink.sarif.message import Message
from .DataTypeProperties import DataTypeProperties


from dataclasses_json import CatchAll, LetterCase, Undefined, dataclass_json


from dataclasses import dataclass


@dataclass_json(undefined=Undefined.INCLUDE, letter_case=LetterCase.CAMEL)
@dataclass
class DataTypeResult:
    message: Message
    ruleId: str
    properties: DataTypeProperties
    extra: CatchAll