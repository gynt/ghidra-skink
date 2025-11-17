from .AdditionalFunctionProperties import AdditionalFunctionProperties


from dataclasses_json import CatchAll, LetterCase, Undefined, dataclass_json


from dataclasses import dataclass


@dataclass_json(undefined=Undefined.INCLUDE, letter_case=LetterCase.CAMEL) # pyright: ignore[reportArgumentType]
@dataclass
class FunctionProperties:
    additionalProperties: AdditionalFunctionProperties
    extra: CatchAll