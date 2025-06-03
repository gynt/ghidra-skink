
from skink.sarif.datatypes.EnumResult import EnumResult
from .symbols.symbol import SymbolResult
from .UnusedResult import UnusedResult
from .datatypes.DataTypeResult import DataTypeResult
from .functions.FunctionResult import FunctionResult


def decode_result(result):
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


def decode_results(results):
    objs = []
    for result in results:
        objs.append(decode_result(result))
    return objs