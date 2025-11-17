from ...sarif.TypeInfo import TypeInfo


from dataclasses_json import CatchAll, LetterCase, Undefined, dataclass_json


from dataclasses import dataclass


@dataclass_json(undefined=Undefined.INCLUDE, letter_case=LetterCase.CAMEL) # pyright: ignore[reportArgumentType]
@dataclass
class StructField:
    offset: int
    type: TypeInfo
    ordinal: int
    length: int    
    name: str
    location: str
    extra: CatchAll
    noFieldName: bool = False
    comment: str = ""
    field_name: str = ""