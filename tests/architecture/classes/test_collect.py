from skink.architecture.classes.cls import Class
from skink.architecture.classes.collect import collect_classes
from skink.architecture.functions.function import Function

namespace = "A::B"

def test_collect1(example_collect_joint_data):
    results = example_collect_joint_data

    classes = collect_classes(results)

    cls = next(classes)
    assert cls.structure is not None
    assert cls.export() == """\
#include "A/B/BStruct.h"
#include "WinDef.h"

namespace A::B {

  class BClass : struct BStruct {

    BOOL  a(undefined4 x, undefined4 y);

    int  b(undefined4 x, undefined4 y);

  }

}\
"""

