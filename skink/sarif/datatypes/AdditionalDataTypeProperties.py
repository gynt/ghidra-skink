from .StructField import StructField


from dataclasses_json import CatchAll, LetterCase, Undefined, dataclass_json


from dataclasses import dataclass
from typing import Dict


@dataclass_json(undefined=Undefined.INCLUDE, letter_case=LetterCase.CAMEL)
@dataclass
class AdditionalDataTypeProperties:
    packed: str
    alignment: str
    kind: str
    size: int
    fields: Dict[str, StructField]
    name: str
    location: str
    extra: CatchAll