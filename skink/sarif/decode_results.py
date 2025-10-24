import logging, json
from typing import Iterable, Dict
from skink.sarif.BasicResult import BasicResult
from skink.sarif.datatypes.EnumResult import EnumResult
from skink.sarif.datatypes.TypedefResult import TypedefResult
from skink.sarif.datatypes.UnionResult import UnionResult
from .symbols.symbol import SymbolResult
from .UnusedResult import UnusedResult
from .datatypes.DataTypeResult import DataTypeResult
from .functions.FunctionResult import FunctionResult
from .defineddata.DefinedDataResult import DefinedDataResult
from .datatypes.FunctionSignatureResult import FunctionSignatureResult

def decode_result(result: Dict) -> BasicResult:
    try:
      if result['ruleId'] == "FUNCTIONS":
          return FunctionResult.from_dict(result) # type: ignore
      elif result['ruleId'] == "DATATYPE":
          if result['message']['text'] == "DT.Enum":
              return EnumResult.from_dict(result) # type: ignore
          elif result['message']['text'] == "DT.Struct":
              return DataTypeResult.from_dict(result) # type: ignore
          elif result['message']['text'] == "DT.Function":
              return FunctionSignatureResult.from_dict(result) # type: ignore
          elif result['message']['text'] == "DT.Union":
              return UnionResult.from_dict(result) # type: ignore
          elif result['message']['text'] == "DT.Typedef":
              return TypedefResult.from_dict(result) # type: ignore
          else:
              pass
              # pass # TODO: print drop of result here
      elif result['ruleId'] == "SYMBOLS":
          return SymbolResult.from_dict(result) # type: ignore
      elif result['ruleId'] == "DEFINED_DATA":
          return DefinedDataResult.from_dict(result) # type: ignore
    except Exception as e:
        raise Exception(f"{e}\nin parsing: {json.dumps(result, indent=2)}")
    logging.log(logging.WARNING, f"unused result: {result['message']['text']}")
    return UnusedResult.from_dict(result) # type: ignore


def decode_results(results: Iterable[Dict]) -> Iterable[BasicResult]:
    objs = []
    for result in results:
        objs.append(decode_result(result))
    return objs