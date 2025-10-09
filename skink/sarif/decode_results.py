import logging
from typing import Iterable, Dict
from skink.sarif.BasicResult import BasicResult
from skink.sarif.datatypes.EnumResult import EnumResult
from .symbols.symbol import SymbolResult
from .UnusedResult import UnusedResult
from .datatypes.DataTypeResult import DataTypeResult
from .functions.FunctionResult import FunctionResult
from .defineddata.DefinedDataResult import DefinedDataResult
from .datatypes.FunctionSignatureResult import FunctionSignatureResult

def decode_result(result: Dict) -> BasicResult:
    if result['ruleId'] == "FUNCTIONS":
        return FunctionResult.from_dict(result) # type: ignore
    elif result['ruleId'] == "DATATYPE":
        if result['message']['text'] == "DT.Enum":
            return EnumResult.from_dict(result) # type: ignore
        elif result['message']['text'] == "DT.Struct":
            return DataTypeResult.from_dict(result) # type: ignore
        elif result['message']['text'] == "DT.Function":
            return FunctionSignatureResult.from_dict(result)
        else:
            pass
            # pass # TODO: print drop of result here
    elif result['ruleId'] == "SYMBOLS":
        return SymbolResult.from_dict(result) # type: ignore
    elif result['ruleId'] == "DEFINED_DATA":
        return DefinedDataResult.from_dict(result)
    logging.log(logging.WARNING, f"unused result: {result['message']['text']}")
    return UnusedResult.from_dict(result) # type: ignore


def decode_results(results: Iterable[Dict]) -> Iterable[BasicResult]:
    objs = []
    for result in results:
        objs.append(decode_result(result))
    return objs