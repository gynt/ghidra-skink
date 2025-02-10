from skink.architecture.functions.function import Function
from skink.architecture.namespaces.namespace import Namespace

namespace = "A::B"

def test_export1(example_class_example_functions_fixture):
    n = Namespace(namespace, [Function(f) for f in example_class_example_functions_fixture])

    e = n.export()

    assert e == """\
#include "A/B/BClass.h"
#include "A/B/BStruct.h"
#include "EXE/WinDef.h"

namespace A::B {

  BOOL __thiscall a(BClass * this, undefined4 x, undefined4 y);

  int __thiscall b(BClass * this, undefined4 x, undefined4 y);

}\
"""