from ..TypeInfo import TypeInfo


from dataclasses_json import CatchAll, LetterCase, Undefined, dataclass_json


from dataclasses import dataclass, field
from typing import List


@dataclass_json(undefined=Undefined.INCLUDE, letter_case=LetterCase.CAMEL) # pyright: ignore[reportArgumentType]
@dataclass
class Param:
    ordinal: int
    size: int
    typeName: str
    typeLocation: str
    type: TypeInfo
    formalTypeName: str
    formalTypeLocation: str
    formalType: TypeInfo
    isAutoParameter: bool
    isForcedIndirect: bool
    stackOffset: int
    name: str
    location: str
    extra: CatchAll
    registers: List[str] = field(default_factory=list)