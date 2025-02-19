from skink.export.context import DEFAULT
from skink.architecture.functions.function import Function

def test_export1(example_class_example_functions_fixture):
    func = example_class_example_functions_fixture[0]
    ff = Function(func)
    ctx = DEFAULT.mutate(include = DEFAULT.include.mutate(functions_this_parameter_type = True))
    e = ff.export(ctx)
    assert e == \
"""\
#include "A/B/BClass.h"
#include "WinDef.h"

namespace A::B {

  BOOL __thiscall a(BClass * this, undefined4 x, undefined4 y);

}\
"""

# TODO: this looks like a circular import to me!
def test_export2(example_class_example_functions_fixture):
    func = example_class_example_functions_fixture[0]
    ff = Function(func)
    ctx = DEFAULT.mutate(promote_to_class = False, include = DEFAULT.include.mutate(functions_this_parameter_type = True))
    e = ff.export(ctx)
    assert e == \
"""\
#include "A/B.h"
#include "WinDef.h"

namespace A::B {

  BOOL __thiscall a(B * this, undefined4 x, undefined4 y);

}\
"""