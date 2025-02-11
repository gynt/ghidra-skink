from .StackVar import StackVar


from dataclasses_json import CatchAll, LetterCase, Undefined, dataclass_json


from dataclasses import dataclass
from typing import List


@dataclass_json(undefined=Undefined.INCLUDE, letter_case=LetterCase.CAMEL)
@dataclass
class Stack:
    stackVars: List[StackVar]
    extra: CatchAll