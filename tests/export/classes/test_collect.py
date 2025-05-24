from skink.export.classes.collect import collect_classes
from skink.sarif.datatypes.DataTypeResult import DataTypeResult

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

def test_collect2(example_collect_joint_data):
    results = example_collect_joint_data

    # What if there is a struct but not associated class...
    results = [result for result in results if isinstance(result, DataTypeResult)]

    classes = list(collect_classes(results))

    assert len(classes) == 0