from skink.architecture.functions.function import Function
from skink.architecture.namespaces.namespace import Namespace
from skink.export.context import DEFAULT

namespace = "A::B"

def test_export1(example_class_example_functions_fixture):
    n = Namespace(namespace, [Function(f) for f in example_class_example_functions_fixture])

    ctx = DEFAULT
    ctx = ctx.mutate(include = ctx.include.mutate(functions_this_parameter_type = True))

    e = n.export(ctx=ctx)

    assert e == """\
#include "A/B/BClass.h"
#include "WinDef.h"

namespace A::B {

  BOOL __thiscall a(BClass * this, undefined4 x, undefined4 y);

  int __thiscall b(BClass * this, undefined4 x, undefined4 y);

}\
"""