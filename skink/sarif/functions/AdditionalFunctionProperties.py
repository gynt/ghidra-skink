from .Param import Param
from .RegVar import RegVar
from .Stack import Stack


from dataclasses_json import CatchAll, LetterCase, Undefined, dataclass_json


from dataclasses import dataclass
from typing import List


@dataclass_json(undefined=Undefined.INCLUDE, letter_case=LetterCase.CAMEL) # pyright: ignore[reportArgumentType]
@dataclass
class AdditionalFunctionProperties:
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