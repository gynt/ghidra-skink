class EncodeContext:
    def __init__(self, decay_arrays=False):
        self.decay_arrays = decay_arrays

class ClassType:
    def __init__(self, ns, name):
        self.ns = ns
        self.name = name

class StructType:
    def __init__(self, ns, name):
        self.ns = ns
        self.name = name

PRIMITIVES = {
    "int": "H",
    "unsigned char": "E",
    "void": "X",
}

class PointerType:
    def __init__(self, typ):
        self.typ = typ

class PrimitiveType:
    def __init__(self, code):
        self.code = code

    @staticmethod
    def from_name(name: str):
        if name not in PRIMITIVES:
            raise Exception(f"type not listed in dictionary: {name}")
        return PrimitiveType(PRIMITIVES[name])

class ArrayType:
    def __init__(self, element, count):
        self.element = element
        self.count = count

MSVC_TO_HEX = {
    chr(ord('A') + i): format(i, 'X')
    for i in range(16)
}

def decode_nttp(s):
    if s == "A":
        return 0

    h = ''.join(
        MSVC_TO_HEX[c]
        for c in s
    )

    return int(h, 16)

HEX_TO_MSVC = {
    format(i, 'X'): chr(ord('A') + i)
    for i in range(16)
}

def encode_hex_number(v):
    h = format(v, 'X')
    return "".join(
        HEX_TO_MSVC[d]
        for d in h
    )

def encode_nttp(v):
    return "$0" + encode_hex_number(v)

def encode_primitive_array(element_code, count, dimensions: int = 0):
    return (
        "$$BY"
        + str(dimensions)
        + encode_hex_number(count)
        + "@"
        + element_code
    )

def encode_pointer(t, ctx):
    return "P" + encode_type(t, ctx)

def encode_class_array(arr: ArrayType, dimensions: int = 0):
    return (
        "$$BY"
        + str(dimensions)
        + encode_hex_number(arr.count)
        + "@"
        + encode_type(arr.element)
    )

def encode_type(t, ctx=None):
    if ctx is None:
        ctx = EncodeContext()

    # ARRAY DECAY RULE
    if isinstance(t, ArrayType) and ctx.decay_arrays:
        return "P" + "A" + encode_type(t.element, ctx)

    if isinstance(t, PrimitiveType):
        return t.code

    if isinstance(t, PointerType):
        return "P" + encode_pointer(t.typ, ctx)

    if isinstance(t, ArrayType):
        # template argument / raw encoding (NO decay)
        return encode_class_array(t)

    prefix = "V"
    if isinstance(t, StructType):
        prefix = "U"
    elif isinstance(t, ClassType):
        prefix = "V"

    return (
        prefix
        + t.name
        + "@"
        + "@".join(reversed(t.ns))
        + "@@"
    )

def encode_extern_instance(typ, address: int):
    # template argument keeps array
    type_tpl = typ

    # symbol exported type decays array → pointer
    type_symbol = typ

    ctx_tpl = EncodeContext(decay_arrays=False)
    ctx_sym = EncodeContext(decay_arrays=True)

    if isinstance(type_symbol, ArrayType):
        type_symbol = PointerType(type_symbol.element)

    return (
        "?instance@"
        "?$Extern@"
        + encode_type(type_tpl, ctx_tpl)
        + encode_nttp(address)
        + "@@StructResolver@@"
        + "2"
        + encode_type(type_symbol, ctx_sym)
        + "A"
    )
