from typing import List, Optional

from skink.sarif.TypeInfo import TypeInfo
from skink.sarif.functions.Param import Param
from skink.sarif.symbols.location import Location

from ..functions.FunctionProperties import FunctionProperties


from dataclasses_json import CatchAll, LetterCase, Undefined, dataclass_json


from dataclasses import dataclass

@dataclass_json(undefined=Undefined.INCLUDE, letter_case=LetterCase.CAMEL)
@dataclass
class FunctionSignatureParam:
    name: str
    size: int
    ordinal: int
    location: str
    kind: str
    extra: CatchAll

@dataclass_json(undefined=Undefined.INCLUDE, letter_case=LetterCase.CAMEL)
@dataclass
class FunctionSignatureRetTypeInfo:
    extra: CatchAll
    kind: str = ""
    name: str = ""
    location: str = ""
    subtype: Optional['TypeInfo'] = None
    size: int = -1
    count: int = -1

@dataclass_json(undefined=Undefined.INCLUDE, letter_case=LetterCase.CAMEL)
@dataclass
class AdditionalFunctionSignatureProperties:
    name: str
    location: str
    kind: str
    callingConventionName: str
    hasVarArgs: bool
    hasNoReturn: bool
    retType: FunctionSignatureRetTypeInfo
    params: List[FunctionSignatureParam]
    extra: CatchAll
    comment: str = ""

@dataclass_json(undefined=Undefined.INCLUDE, letter_case=LetterCase.CAMEL)
@dataclass
class FunctionSignatureProperties:
    additionalProperties: AdditionalFunctionSignatureProperties
    extra: CatchAll

@dataclass_json(undefined=Undefined.INCLUDE, letter_case=LetterCase.CAMEL)
@dataclass
class FunctionSignatureResult:
    ruleId: str
    properties: FunctionSignatureProperties
    extra: CatchAll