
from typing import Iterable, Dict
from skink.sarif.BasicResult import BasicResult
from skink.sarif.datatypes.EnumResult import EnumResult
from .symbols.symbol import SymbolResult
from .UnusedResult import UnusedResult
from .datatypes.DataTypeResult import DataTypeResult
from .functions.FunctionResult import FunctionResult


def decode_result(result: Dict) -> BasicResult:
    if result['ruleId'] == "FUNCTIONS":
        return FunctionResult.from_dict(result) # type: ignore
    elif result['ruleId'] == "DATATYPE":
        if result['message']['text'] == "DT.Enum":
            return EnumResult.from_dict(result) # type: ignore
        elif result['message']['text'] == "DT.Struct":
            return DataTypeResult.from_dict(result) # type: ignore
        else:
            pass
            # pass # TODO: print drop of result here
    elif result['ruleId'] == "SYMBOLS":
        return SymbolResult.from_dict(result) # type: ignore
    return UnusedResult.from_dict(result) # type: ignore


def decode_results(results: Iterable[Dict]) -> Iterable[BasicResult]:
    objs = []
    for result in results:
        objs.append(decode_result(result))
    return objs