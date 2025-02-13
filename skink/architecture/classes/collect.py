from dataclasses import dataclass, field
import dataclasses
from typing import Dict, List

from dataclasses_json import dataclass_json
from skink.architecture.functions.function import Function
from skink.architecture.structs.struct import Struct
from skink.export.location import normalize_location
from skink.sarif import SarifExport
from skink.sarif.BasicResult import BasicResult
from skink.sarif.datatypes.AdditionalDataTypeProperties import AdditionalDataTypeProperties
from skink.sarif.datatypes.DataTypeResult import DataTypeResult
from skink.sarif.functions.AdditionalFunctionProperties import AdditionalFunctionProperties
from skink.sarif.functions.FunctionResult import FunctionResult
from .cls import Class

@dataclass_json
@dataclass
class PreClass:
    namespace: str
    functions: List[FunctionResult] = field(default_factory=list)
    structure: DataTypeResult = None

def collect_classes(results: List[BasicResult]):
    classes: Dict[str, PreClass] = {}
    for result in results:
        if isinstance(result, FunctionResult):
            ap: AdditionalFunctionProperties = result.properties.additionalProperties
            if ap.namespaceIsClass:
                ns = ap.namespace
                if not ns in classes:
                    classes[ns] = PreClass(ns)
                classes[ns].functions.append(result)
        elif isinstance(result, DataTypeResult):
            ap: AdditionalDataTypeProperties = result.properties.additionalProperties
            loc = normalize_location(ap.location) + f"/{ap.name}"
            ns = loc.replace("/", "::")
            if not ns in classes:
                classes[ns] = PreClass(ns)
            if classes[ns].structure:
                raise Exception("structure already set")
            # TODO: is this dirty? We promote this struct to a class struct and therefore move it next to the cls file
            ap.location = loc
            classes[ns].structure = result
    for ns, preclass in classes.items():
        functions = [Function(fr) for fr in preclass.functions]
        struct = None
        if preclass.structure:
            struct = Struct(preclass.structure)
        yield Class(ns, functions, struct)
    
def collect_classes_from_export(se: SarifExport):
    return collect_classes(se.runs[0].results)