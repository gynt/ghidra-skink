from typing import List
from skink.architecture.classes.cls import Class
from skink.architecture.export.context import DEFAULT, Context
from skink.architecture.functions.function import Function
from skink.architecture.namespaces.namespace import Namespace
from skink.sarif import FunctionResult, SarifExport
import json


with open("data/class-example.sarif.json", 'r') as f:
    j = json.load(f)
    sarifExport: SarifExport = SarifExport.from_dict(j)
    vprs_functions = [f for f in sarifExport.runs[0].results if f.ruleId == "FUNCTIONS"]

namespace = "A::B"
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
ctx = ctx.mutate(function_rules = ctx.function_rules.mutate(virtual = True))
ctx = ctx.mutate(class_rules = ctx.class_rules.mutate(prefix = "_"))
print(ctx.to_json())
print(c.export(ctx))
