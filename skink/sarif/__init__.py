from dataclasses import dataclass, field
from dataclasses_json import CatchAll, config, Undefined, dataclass_json, LetterCase
from typing import List, Dict, Any, Optional

@dataclass_json(undefined=Undefined.INCLUDE, letter_case=LetterCase.CAMEL)
@dataclass
class TypeInfo:
    kind: str
    size: int
    name: str
    location: str
    extra: CatchAll

@dataclass_json(undefined=Undefined.INCLUDE, letter_case=LetterCase.CAMEL)
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

@dataclass_json(undefined=Undefined.INCLUDE, letter_case=LetterCase.CAMEL)
@dataclass
class RegVar:
    register: str
    size: int
    typeName: str
    typeLocation: str
    type: TypeInfo
    name: str
    location: str
    extra: CatchAll

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

@dataclass_json(undefined=Undefined.INCLUDE, letter_case=LetterCase.CAMEL)
@dataclass
class Stack:
    stackVars: List[StackVar]
    extra: CatchAll

@dataclass_json(undefined=Undefined.INCLUDE, letter_case=LetterCase.CAMEL)
@dataclass
class AdditionalProperties:
    name: str
    location: str
    callingConvention: str
    namespaceIsClass: bool
    stack: Stack
    regVars: List[RegVar]
    ret: Param
    params: List[Param]
    extra: CatchAll
    namespace: str = ""
    value: str = ""
    type: str = ""

@dataclass_json(undefined=Undefined.INCLUDE, letter_case=LetterCase.CAMEL)
@dataclass
class Properties:
    additionalProperties: AdditionalProperties
    extra: CatchAll

@dataclass_json(undefined=Undefined.INCLUDE, letter_case=LetterCase.CAMEL)
@dataclass
class FunctionResult:
    ruleId: str
    properties: Properties
    extra: CatchAll

@dataclass_json(undefined=Undefined.INCLUDE, letter_case=LetterCase.CAMEL)
@dataclass
class UnusedResult:
    ruleId: str
    extra: CatchAll

def decode_result(result):
    if result['ruleId'] == "FUNCTIONS":
        return FunctionResult.from_dict(result)
    else:
        return UnusedResult.from_dict(result)

def decode_results(results):
    objs = [] 
    for result in results:
        objs.append(decode_result(result))
    return objs

@dataclass_json(undefined=Undefined.INCLUDE, letter_case=LetterCase.CAMEL)
@dataclass
class Run:
    results: List[FunctionResult] = field(metadata=config(decoder=decode_results))
    extra: CatchAll

@dataclass_json(undefined=Undefined.INCLUDE, letter_case=LetterCase.CAMEL)
@dataclass
class SarifExport:
    runs: List[Run]
    extra: CatchAll

