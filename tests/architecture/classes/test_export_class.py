from skink.architecture.classes.cls import Class
from skink.architecture.functions.function import Function

namespace = "A::B"

def test_export1(example_class_example_functions_fixture):
    c = Class(namespace, [Function(f) for f in example_class_example_functions_fixture])

    e = c.export()

    assert e == """\
#include "A/B/BStruct.h"
#include "WinDef.h"

namespace A::B {

  class BClass : struct BStruct {

    BOOL  a(undefined4 x, undefined4 y);

    int  b(undefined4 x, undefined4 y);

  }

}\
"""