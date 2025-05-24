from dataclasses_json import CatchAll, LetterCase, Undefined, dataclass_json


from dataclasses import dataclass


@dataclass_json(undefined=Undefined.INCLUDE, letter_case=LetterCase.CAMEL)
@dataclass
class Address:
  absoluteAddress: int
  length: int
  extra: CatchAll


@dataclass_json(undefined=Undefined.INCLUDE, letter_case=LetterCase.CAMEL)
@dataclass
class PhysicalLocation:
  address: Address
  extra: CatchAll


@dataclass_json(undefined=Undefined.INCLUDE, letter_case=LetterCase.CAMEL)
@dataclass
class Location:
  physicalLocation: PhysicalLocation
  extra: CatchAll