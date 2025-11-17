from ..defineddata.AdditionalDefinedDataProperties import AdditionalDefinedDataProperties
from skink.sarif.message import Message

from dataclasses_json import CatchAll, LetterCase, Undefined, dataclass_json


from dataclasses import dataclass


@dataclass_json(undefined=Undefined.INCLUDE, letter_case=LetterCase.CAMEL) # pyright: ignore[reportArgumentType]
@dataclass
class DefinedDataProperties:
  additionalProperties: AdditionalDefinedDataProperties
  extra: CatchAll