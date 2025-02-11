
from .UnusedResult import UnusedResult
from .datatypes.DataTypeResult import DataTypeResult
from .functions.FunctionResult import FunctionResult


def decode_result(result):
    if result['ruleId'] == "FUNCTIONS":
        return FunctionResult.from_dict(result)
    elif result['ruleId'] == "DATATYPE":
        return DataTypeResult.from_dict(result)
    else:
        return UnusedResult.from_dict(result)


def decode_results(results):
    objs = []
    for result in results:
        objs.append(decode_result(result))
    return objs