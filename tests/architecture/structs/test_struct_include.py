from skink.architecture.classes.cls import Class
from skink.export.context import DEFAULT
from skink.architecture.functions.function import Function
from skink.architecture.structs.struct import Struct

namespace = "A::B"

def test_struct_include1(example_struct_example_fixture):
    c = [Struct(f) for f in example_struct_example_fixture][0]

    e = c.include()

    assert e == '#include "Structs/Struct1Struct.h"'