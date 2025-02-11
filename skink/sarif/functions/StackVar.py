from ..TypeInfo import TypeInfo


from dataclasses_json import CatchAll, LetterCase, Undefined, dataclass_json


from dataclasses import dataclass


@dataclass_json(undefined=Undefined.INCLUDE, letter_case=LetterCase.CAMEL)
@dataclass
class StackVar:
    size: int
    offset: int
    typeName: str
    typeLocation: str
    type: TypeInfo
    name: str
    location: str
    extra: CatchAll