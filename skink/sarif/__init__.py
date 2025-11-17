from dataclasses import dataclass
from dataclasses_json import CatchAll, Undefined, dataclass_json, LetterCase
from typing import List

from skink.sarif.Run import Run

@dataclass_json(undefined=Undefined.INCLUDE, letter_case=LetterCase.CAMEL) # pyright: ignore[reportArgumentType]
@dataclass
class SarifExport:
    runs: List[Run]
    extra: CatchAll

