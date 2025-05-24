from skink.export.classes.collect import collect_classes
from skink.export.context import DEFAULT

def test_export_inline1(example_collect_joint_data):
    results = example_collect_joint_data

    classes = collect_classes(results)

    ctx = DEFAULT
    ctx.class_rules = ctx.class_rules.mutate(inline_struct = True)

    cls = next(classes)
    assert cls.structure is not None
    assert cls.export(ctx=ctx) == """\
#include "WinDef.h"
#include "A/B/Enum1.h"

namespace A::B {

  class BClass {

    dword a;

    dword b;

    dword c;

    dword d;

    dword e;

    dword f;

    Enum1 g;

    BOOL  a(undefined4 x, undefined4 y);

    int  b(undefined4 x, undefined4 y);

  }

}\
"""