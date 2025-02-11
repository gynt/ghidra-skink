from skink.architecture.classes.cls import Class
from skink.export.context import DEFAULT
from skink.architecture.functions.function import Function

namespace = "A::B"

def test_export1(example_class_example_functions_fixture):
    c = Class(namespace, [Function(f) for f in example_class_example_functions_fixture])
    ctx = DEFAULT
    ctx = ctx.mutate(function_rules = ctx.function_rules.mutate(virtual = True))
    ctx = ctx.mutate(class_rules = ctx.class_rules.mutate(prefix = "_"))
    e = c.export(ctx)

    assert e == """\
#include "A/B/BStruct.h"
#include "WinDef.h"

namespace A::B {

  class _BClass : struct BStruct {

    virtual BOOL  a(undefined4 x, undefined4 y) = 0;

    virtual int  b(undefined4 x, undefined4 y) = 0;

  }

}\
"""