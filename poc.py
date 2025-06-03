from typing import List
from skink.architecture.classes.cls import Class
from skink.architecture.export.context import DEFAULT, Context
from skink.architecture.functions.function import Function
from skink.architecture.namespaces.namespace import Namespace
from skink.sarif import SarifExport
import json

from skink.sarif.FunctionResult import FunctionResult


with open("data/class-example.sarif.json", 'r') as f:
    j = json.load(f)
    sarifExport: SarifExport = SarifExport.from_dict(j)
    vprs_functions = [f for f in sarifExport.runs[0].results if f.ruleId == "FUNCTIONS"]

namespace = "A::B"
classs = namespace + "Class"
struct = namespace + "Struct"
func = vprs_functions[0]
ff = Function(func)

log(logging.DEBUG, ff.export())

n = Namespace(namespace, [Function(f) for f in vprs_functions])

log(logging.DEBUG, n.export())

c = Class(namespace, [Function(f) for f in vprs_functions])

log(logging.DEBUG, c.export())

ctx = DEFAULT
ctx = ctx.mutate(function_rules = ctx.function_rules.mutate(virtual = True))
ctx = ctx.mutate(class_rules = ctx.class_rules.mutate(prefix = "_"))
log(logging.DEBUG, ctx.to_json())
log(logging.DEBUG, c.export(ctx))
