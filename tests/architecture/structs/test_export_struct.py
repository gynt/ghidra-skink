from skink.export.context import DEFAULT
from skink.architecture.structs.struct import Struct

namespace = "A::B"

def test_export1(example_struct_example_fixture):
    c = [Struct(f) for f in example_struct_example_fixture][0]

    e = c.export()

    assert e == """\
#include "Structs/Struct1/Enum1.h"

namespace Structs {

  struct Struct1Struct {

    dword a;

    dword b;

    dword c;

    dword d;

    dword e;

    dword f;

    Enum1 g;

  };

}\
"""

def test_export2(example_struct_example_fixture):
    c = [Struct(f) for f in example_struct_example_fixture][0]

    e = c.export(DEFAULT.mutate(struct_rules = DEFAULT.struct_rules.mutate(typedef = True, suffix = "", prefix = "_")))

    assert e == """\
#include "Structs/Struct1/Enum1.h"

namespace Structs {

  typedef struct _Struct1 {

    dword a;

    dword b;

    dword c;

    dword d;

    dword e;

    dword f;

    Enum1 g;

  } _Struct1;

}\
"""