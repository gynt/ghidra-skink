from dataclasses import dataclass, field
import dataclasses
from typing import Dict, List

from dataclasses_json import dataclass_json
from skink.architecture.functions.function import Function
from skink.architecture.structs.struct import Struct
from skink.sarif import SarifExport
from skink.sarif.datatypes import AdditionalDataTypeProperties, DataTypeResult
from skink.sarif.functions import AdditionalFunctionProperties
from skink.sarif.functions.FunctionResult import FunctionResult
from .cls import Class

@dataclass_json
@dataclass
class PreClass:
    namespace: str
    functions: List[FunctionResult] = field(default_factory=lambda: list)
    structure: DataTypeResult = None

def collect_classes(se: SarifExport):
    classes: Dict[str, PreClass] = {}
    for result in se.runs[0].results:
        if isinstance(result, FunctionResult):
            ap: AdditionalFunctionProperties = result.properties.additionalProperties
            if ap.namespaceIsClass:
                ns = ap.namespace
                if not ns in classes:
                    classes[ns] = PreClass(ns)
                classes[ns].functions.append(result)
        elif isinstance(result, DataTypeResult):
            ap: AdditionalDataTypeProperties = result.properties.additionalProperties
            ns = ap.location.split.replace("/", "::")
            if not ns in classes:
                classes[ns] = PreClass(ns)
            if classes[ns].structure:
                raise Exception("structure already set")
            classes[ns].structure = result
    for ns, preclass in classes.items():
        functions = [Function(fr) for fr in preclass.functions]
        struct = Struct(preclass.structure)
        return Class(ns, functions, struct)