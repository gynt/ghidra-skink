from ...sarif.TypeInfo import TypeInfo


from dataclasses_json import CatchAll, LetterCase, Undefined, dataclass_json


from dataclasses import dataclass


@dataclass_json(undefined=Undefined.INCLUDE, letter_case=LetterCase.CAMEL)
@dataclass
class StructField:
    offset: int
    type: TypeInfo
    ordinal: int
    length: int
    field_name: str
    name: str
    location: str
    extra: CatchAll