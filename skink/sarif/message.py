

from dataclasses import dataclass
from dataclasses_json import CatchAll, LetterCase, Undefined, dataclass_json


@dataclass_json(undefined=Undefined.INCLUDE, letter_case=LetterCase.CAMEL)
@dataclass
class Message:
  text: str
  extra: CatchAll