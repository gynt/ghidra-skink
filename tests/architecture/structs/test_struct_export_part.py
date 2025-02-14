from skink.architecture.classes.cls import Class
from skink.export.context import DEFAULT
from skink.architecture.functions.function import Function
from skink.architecture.structs.struct import Struct

namespace = "A::B"

def test_struct_export_part1(example_struct_example_fixture):
    c = [Struct(f) for f in example_struct_example_fixture][0]

    e = c.export_fields()

    assert '\n'.join(e.fields) == """\
dword a;
dword b;
dword c;
dword d;
dword e;
dword f;
Enum1 g;\
"""
    assert '\n'.join(e.includes) == """\
#include "Structs/Struct1/Enum1.h"\
"""
