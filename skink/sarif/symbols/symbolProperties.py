

from dataclasses_json import CatchAll, LetterCase, Undefined, dataclass_json


from dataclasses import dataclass


@dataclass_json(undefined=Undefined.INCLUDE, letter_case=LetterCase.CAMEL)
@dataclass
class AdditionalSymbolProperties:
  name: str
  location: str # ends with :: if a namespace, else ""
  kind: str
  sourceType: str
  primary: bool
  pinned: bool
  extra: CatchAll
  type: str = ""
  namespaceIsClass: bool = False


@dataclass_json(undefined=Undefined.INCLUDE, letter_case=LetterCase.CAMEL)
@dataclass
class SymbolProperties:
  additionalProperties: AdditionalSymbolProperties
  extra: CatchAll