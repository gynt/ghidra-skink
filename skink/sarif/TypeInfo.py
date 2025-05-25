from typing import List, Optional
from dataclasses_json import CatchAll, LetterCase, Undefined, dataclass_json


from dataclasses import dataclass

@dataclass_json(undefined=Undefined.INCLUDE, letter_case=LetterCase.CAMEL)
@dataclass
class Settings:
    name: str
    kind: str
    value: str
    extra: CatchAll

@dataclass_json(undefined=Undefined.INCLUDE, letter_case=LetterCase.CAMEL)
@dataclass
class TypeInfo:
    kind: str
    name: str
    extra: CatchAll
    location: str = ""
    settings: Optional[List[Settings]] = None
    subtype: Optional['TypeInfo'] = None
    size: int = -1
    count: int = -1
    