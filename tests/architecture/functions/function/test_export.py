from skink.architecture.functions.function import Function


def test_export1(example_class_example_functions_fixture):
    func = example_class_example_functions_fixture[0]
    ff = Function(func)
    e = ff.export()
    assert e == \
"""\
#include "EXE/A/B.h"
#include "EXE/WinDef.h"

namespace A::B {

  BOOL __thiscall a(BClass * this, undefined4 x, undefined4 y);

}\
"""