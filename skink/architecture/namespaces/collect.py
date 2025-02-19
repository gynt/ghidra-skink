from dataclasses import dataclass, field
from typing import Dict, List

from dataclasses_json import dataclass_json
from skink.architecture.functions.function import Function
from skink.architecture.namespaces.namespace import Namespace
from skink.architecture.structs.struct import Struct
from skink.export.location import normalize_location
from skink.sarif import SarifExport
from skink.sarif.BasicResult import BasicResult
from skink.sarif.datatypes.AdditionalDataTypeProperties import AdditionalDataTypeProperties
from skink.sarif.datatypes.DataTypeResult import DataTypeResult
from skink.sarif.functions.AdditionalFunctionProperties import AdditionalFunctionProperties
from skink.sarif.functions.FunctionResult import FunctionResult

@dataclass_json
@dataclass
class PreNamespace:
    namespace: str
    functions: List[FunctionResult] = field(default_factory=list)
    structures: List[DataTypeResult] = field(default_factory=list)

def collect_namespaces(results: List[BasicResult]):
    namespaces: Dict[str, PreNamespace] = {}
    for result in results:
        if isinstance(result, FunctionResult):
            ap: AdditionalFunctionProperties = result.properties.additionalProperties
            if not ap.namespaceIsClass:
                ns = ap.namespace
                if not ns in namespaces:
                    namespaces[ns] = PreNamespace(ns)
                namespaces[ns].functions.append(result)
        elif isinstance(result, DataTypeResult):
            ap: AdditionalDataTypeProperties = result.properties.additionalProperties
            loc = normalize_location(ap.location) + f"/{ap.name}"
            ns = loc.replace("/", "::")
            if not ns in namespaces:
                namespaces[ns] = PreNamespace(ns)
            # TODO: is this valid? or do we need / instead of ::
            # ap.location = loc
            namespaces[ns].structures.append(result)
            # TODO: implement global variables?
    for ns, prenamespace in namespaces.items():
        functions = [Function(fr) for fr in prenamespace.functions]
        structures = [Struct(sr) for sr in prenamespace.structures]
        yield Namespace(ns, functions, structures)
    
def collect_namespaces_from_export(se: SarifExport):
    return collect_namespaces(se.runs[0].results)