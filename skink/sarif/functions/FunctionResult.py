from .FunctionProperties import FunctionProperties


from dataclasses_json import CatchAll, LetterCase, Undefined, dataclass_json


from dataclasses import dataclass


@dataclass_json(undefined=Undefined.INCLUDE, letter_case=LetterCase.CAMEL)
@dataclass
class FunctionResult:
    ruleId: str
    properties: FunctionProperties
    extra: CatchAll