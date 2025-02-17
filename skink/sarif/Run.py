from skink.sarif.BasicResult import BasicResult
from .decode_results import decode_results


from dataclasses_json import CatchAll, LetterCase, Undefined, config, dataclass_json


from dataclasses import dataclass, field
from typing import List


@dataclass_json(undefined=Undefined.INCLUDE, letter_case=LetterCase.CAMEL)
@dataclass
class Run:
    results: List[BasicResult] = field(metadata=config(decoder=decode_results))
    extra: CatchAll