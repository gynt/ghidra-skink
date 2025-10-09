from typing import List

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

@dataclass_json(undefined=Undefined.INCLUDE, letter_case=LetterCase.CAMEL)
@dataclass
class AdditionalFunctionSignatureProperties:
    name: str
    location: str
    callingConventionName: str
    hasVarArgs: bool
    hasNoReturn: bool
    retType: TypeInfo
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