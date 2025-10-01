from skink.sarif.message import Message

from dataclasses_json import CatchAll, LetterCase, Undefined, dataclass_json


from dataclasses import dataclass


@dataclass_json(undefined=Undefined.INCLUDE, letter_case=LetterCase.CAMEL)
@dataclass
class AdditionalDefinedDataProperties:
  typeName: str
  typeLocation: str
  name: str
  location: str
  # we ignore "nested" which contains comments
  extra: CatchAll