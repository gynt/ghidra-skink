from typing import List
from skink.architecture.classes.cls import Class
from skink.architecture.export.context import DEFAULT
from skink.architecture.functions.function import Function
from skink.architecture.namespaces.namespace import Namespace
from skink.sarif import FunctionResult, SarifExport
import json

# with open("data/Stronghold Crusader.exe.functions.sarif", 'rb') as f:
#     validation = SarifExport.schema().validate(json.load(f))

# with open("data/Stronghold Crusader.exe.functions.sarif", 'rb') as f:
#     s: SarifExport = SarifExport.schema().loads(f.read())

# class_functions: List[FunctionResult] = [r for r in s.runs[0].results if r.ruleId == "FUNCTIONS" and r.properties.additionalProperties.namespaceIsClass]
# classes = set(f.properties.additionalProperties.namespace for f in class_functions)

# with open("data/ViewportRenderState-functions.json", 'w') as f:
#     f.write(f"[{', '.join(v.to_json() for v in vprs_functions)}]")


with open("data/ViewportRenderState-functions.json", 'r') as f:
    j = json.load(f)
    vprs_functions = [FunctionResult.from_dict(d) for d in j]


# functions = [r for r in s.runs[0].results if r.ruleId == "FUNCTIONS"]
# class_functions = [f for f in functions if f.properties.additionalProperties.namespaceIsClass]
# func = functions[100]

namespace = "_HoldStrong::ViewportRenderState"
classs = namespace + "Class"
struct = namespace + "Struct"
func = vprs_functions[0]
ff = Function(func)

print(ff.export())

n = Namespace(namespace, [Function(f) for f in vprs_functions])

print(n.export())

c = Class(namespace, [Function(f) for f in vprs_functions])

print(c.export())

ctx = DEFAULT
ctx = ctx.mutate("function_rules", ctx.function_rules.mutate("virtual", True))
ctx = ctx.mutate("class_rules", ctx.class_rules.mutate("prefix", "_"))
print(c.export(ctx))
