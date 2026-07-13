#!/usr/bin/env python3
"""
MSVC 1400 symbol mangler for StructResolver::Extern<T, N>::instance variables.

Usage:
    python msvc_mangler.py                 # runs built-in self-test
    python msvc_mangler.py input.txt       # reads "decl" -> "expected" pairs (one per line)
    python msvc_mangler.py --gen decl.txt  # reads declarations, prints mangled symbols

Input format for validation mode (input.txt):
    One entry per line, two quoted strings separated by whitespace:
        "public: static int StructResolver::Extern<int,42>::instance"  (?expected_symbol)

    OR plain lines with just the declaration string (--gen mode).
"""

import re
import sys
from dataclasses import dataclass
from typing import List, Tuple, Optional


# ---------------------------------------------------------------------------
# Encoding tables
# ---------------------------------------------------------------------------

# Maps hex digit (str) -> mangling char
_HEX_DIGIT_TO_CHAR = {format(i, 'X'): chr(ord('A') + i) for i in range(16)}

# For values 0-15, the mapping is NOT just the hex->char table above.
# Values  0     -> 'A'
# Values  1-10  -> '0'-'9'  (decimal digits!)
# Values 11-15  -> 'L'-'P'
_SMALL_TABLE = ["A", "0", "1", "2", "3", "4", "5", "6", "7", "8",
                "9", "L", "M", "N", "O", "P"]

PRIMITIVES = {
    "void":           "X",
    "char":           "D",
    "signed char":    "C",
    "unsigned char":  "E",
    "short":          "F",
    "unsigned short": "G",
    "int":            "H",
    "BOOL":           "H",
    "unsigned int":   "I",
    "long":           "J",
    "unsigned long":  "K",
    "float":          "M",
    "double":         "N",
    "bool":          "_N",
    "wchar_t":       "_W",
    "WCHAR":         "_W",
}

# ---------------------------------------------------------------------------
# Core number encoding
# ---------------------------------------------------------------------------

def encode_hex_number(v: int) -> str:
    """
    Encode a non-negative integer in MSVC's base-16 letter/digit scheme.

    0  -> 'A'
    1  -> '0'
    2  -> '1'
    ...
    10 -> '9'
    11 -> 'L'
    ...
    15 -> 'P'
    16 -> 'BA'   (hex 0x10 -> digits '1','0' -> 'B','A')
    255 -> 'PP'
    ...
    """
    if v < 16:
        return _SMALL_TABLE[v]
    h = format(v, 'X')
    return "".join(_HEX_DIGIT_TO_CHAR[d] for d in h)


def encode_integral(n: int) -> str:
    """
    Encode an integer template non-type parameter as '$0<encoded>'.
    The trailing '@' separator is NOT included here; the caller adds it.
    """
    return "$0" + encode_hex_number(n)


# ---------------------------------------------------------------------------
# Array-dimension encoding
# ---------------------------------------------------------------------------

def encode_dim(n: int) -> str:
    """
    Encode a single array dimension for use inside $$BY/Y sequences.

    Rule: encode the number, then append '@' UNLESS the result is a pure
    digit string (digits '0'-'9' only).  Pure-digit results come from
    values 1-10 and need no terminator because they are self-delimiting.
    """
    s = encode_hex_number(n)
    if not s.isdigit():
        s += '@'
    return s


# ---------------------------------------------------------------------------
# Type AST helpers  (simple tuples, no classes needed)
#
#  ('prim', name)                   primitive type
#  ('user', tag, parts)             struct/class/union  tag in {U,V,T}
#  ('ptr', target)                  pointer-to-target
#  ('arr', element, [d1, d2, ...])  array
# ---------------------------------------------------------------------------

def encode_user_name(parts: List[str]) -> str:
    """Reverse the scope chain and join with '@', ending with '@@'."""
    return "@".join(reversed(parts)) + "@@"


def encode_type_as_template_arg(t) -> str:
    """
    Encode a type for use as a template argument (uses $$BY for arrays).
    """
    k = t[0]
    if k == 'prim':
        return PRIMITIVES[t[1]]
    if k == 'user':
        _, tag, parts = t
        return tag + encode_user_name(parts)
    if k == 'ptr':
        return "PA" + encode_type_as_template_arg(t[1])
    if k == 'arr':
        _, elem, dims = t
        rank = len(dims)
        dim_str = "".join(encode_dim(d) for d in dims)
        return f"$$BY{rank - 1}{dim_str}{encode_type_as_template_arg(elem)}"
    raise TypeError(f"unknown type node: {t!r}")


def decay(t) -> tuple:
    """
    Compute the type of StructResolver::Extern<T, N>::instance.

    For array T[d0][d1]...: the member is a pointer to T[d1]...
    For anything else: it's just T.
    """
    if t[0] == 'arr':
        _, elem, dims = t
        inner = elem if len(dims) == 1 else ('arr', elem, dims[1:])
        return ('ptr', inner)
    return t


def encode_type_as_instance(t) -> str:
    """
    Encode a type for use as the type of the static member (after decay).
    Arrays here use 'Y' (not '$$BY').
    """
    k = t[0]
    if k == 'prim':
        return PRIMITIVES[t[1]]
    if k == 'user':
        _, tag, parts = t
        return tag + encode_user_name(parts)
    if k == 'ptr':
        inner = t[1]
        return "PA" + encode_type_as_instance(inner)
    if k == 'arr':
        _, elem, dims = t
        rank = len(dims)
        dim_str = "".join(encode_dim(d) for d in dims)
        return f"Y{rank - 1}{dim_str}{encode_type_as_instance(elem)}"
    raise TypeError(f"unknown type node: {t!r}")


# ---------------------------------------------------------------------------
# Symbol construction
# ---------------------------------------------------------------------------

def build_extern_symbol(type_ast, integral_arg: int) -> str:
    """
    Build the full mangled name for:
        StructResolver::Extern<type_ast, integral_arg>::instance
    """
    tmpl_enc  = encode_type_as_template_arg(type_ast)
    inst_type = decay(type_ast)
    inst_enc  = encode_type_as_instance(inst_type)
    nttp      = encode_integral(integral_arg)

    return (
        "?instance@?$Extern@"
        + tmpl_enc
        + nttp
        + "@@StructResolver@@2"
        + inst_enc
        + "A"
    )


# ---------------------------------------------------------------------------
# Declaration parser
# ---------------------------------------------------------------------------

# Regex to detect array suffix(es) on a type, e.g. "[64]" or "[33][1024]"
_ARRAY_SUFFIX_RE = re.compile(r'^(.*?)\s*((?:\[\d+\])+)$', re.DOTALL)

# Scoped name in C++ source, e.g. "OpenSHC::UI::MenuView"
_SCOPED_NAME_RE = re.compile(r'[A-Za-z_]\w*(?:::[A-Za-z_]\w*)*')


def _split_scoped(name: str) -> List[str]:
    return name.split("::")


def _parse_type(s: str) -> tuple:
    """
    Parse a C++ type string into a type AST tuple.
    Handles:
      * primitives (int, char, float, …)
      * wchar_t
      * void *
      * pointer types (T *)
      * array types (T [N] or T [N][M]…)
      * struct/class/union UserType
      * pointer to user type (struct Foo *)
      * pointer to pointer (struct Foo * *)
    """
    s = s.strip()

    # ---- pointer-to-pointer:  "struct Foo * *" or "void * *"
    if s.endswith('* *') or re.search(r'\*\s*\*\s*$', s):
        inner_str = re.sub(r'\s*\*\s*$', '', s).rstrip()
        return ('ptr', _parse_type(inner_str))

    # ---- plain pointer: ends with '*'
    if s.endswith('*'):
        inner_str = s[:-1].rstrip()
        return ('ptr', _parse_type(inner_str))

    # ---- array: ends with [...]
    m = _ARRAY_SUFFIX_RE.match(s)
    if m:
        base_str = m.group(1)
        dims = [int(x) for x in re.findall(r'\[(\d+)\]', m.group(2))]
        return ('arr', _parse_type(base_str), dims)

    # ---- primitives
    if s in PRIMITIVES:
        return ('prim', s)

    # ---- user-defined type:  "struct Foo", "class Bar", "union Baz"
    m2 = re.match(r'^(struct|class|union)\s+(.+)$', s)
    if m2:
        kind, name = m2.group(1), m2.group(2).strip()
        tag = {'struct': 'U', 'class': 'V', 'union': 'T'}[kind]
        return ('user', tag, _split_scoped(name))

    # ---- bare class/struct name without keyword (shouldn't appear in these decls, but handle it)
    raise ValueError(f"cannot parse type: {s!r}")


# Regex for the full declaration:
#   "public: static <type> StructResolver::Extern<<template_type>,<N>>::instance"
# or (for pointer-to-array return types):
#   "public: static <elem_type> (* StructResolver::Extern<<template_type>,<N>>::instance)[dims]"
_DECL_RE = re.compile(
    r'"public: static\s+'
    r'(.+?)'               # group 1: return/variable type (may include (* ... ) syntax)
    r'\s+StructResolver::Extern<'
    r'(.+?)'               # group 2: template type arg
    r',(\d+)'              # group 3: template integral arg
    r'>::instance'
    r'(?:\s*\)\s*(\[[\d\]\[]+\]))?'  # group 4: optional trailing [dims] for ptr-to-array
    r'"'
)

# Alternative: the "(* ... )[dims]" form
_DECL_PTR_ARR_RE = re.compile(
    r'"public: static\s+'
    r'(.+?)'               # group 1: element type
    r'\s+\(\*\s+StructResolver::Extern<'
    r'(.+?)'               # group 2: template type arg (redundant here but parsed)
    r',(\d+)'              # group 3: N
    r'>::instance\)'
    r'(\[[\d\]\[]+\])'     # group 4: trailing dims
    r'"'
)


def parse_declaration(decl: str) -> Tuple[tuple, int]:
    """
    Parse a C++ declaration string and return (type_ast, integral_N).

    Handles two surface forms:
      "public: static T StructResolver::Extern<T, N>::instance"
      "public: static E (* StructResolver::Extern<E[D0][D1...], N>::instance)[D1...]"
    """
    decl = decl.strip().strip('"')

    # ---- pointer-to-array form:
    #   "public: static short (* StructResolver::Extern<short [33][64][4],N>::instance)[64][4]"
    m = re.match(
        r'public: static\s+'
        r'(.+?)'                           # element type, e.g. "short"
        r'\s+\(\*\s+StructResolver::Extern<'
        r'(.+?)'                           # full template type
        r',\s*(\d+)'
        r'>::instance\)'
        r'(\[[\d\]\[]+\])',                # trailing dims like [64][4]
        decl
    )
    if m:
        # The template type arg string (group 2) fully describes the array type
        tmpl_type_str = m.group(2).strip()
        n = int(m.group(3))
        type_ast = _parse_type(tmpl_type_str)
        return type_ast, n

    # ---- normal form
    m = re.match(
        r'public: static\s+'
        r'(.+?)'                           # variable type
        r'\s+StructResolver::Extern<'
        r'(.+?)'                           # template type
        r',\s*(\d+)'
        r'>::instance"?$',
        decl
    )
    if m:
        tmpl_type_str = m.group(2).strip()
        n = int(m.group(3))
        type_ast = _parse_type(tmpl_type_str)
        return type_ast, n

    raise ValueError(f"cannot parse declaration: {decl!r}")


# ---------------------------------------------------------------------------
# File-level processing
# ---------------------------------------------------------------------------

def process_line(line: str):
    """
    Process one line from the input file.
    Expected format:
        "public: static ... ::instance"  (?mangled_name)
    or just:
        "public: static ... ::instance"
    Returns (declaration_str, expected_or_None, got_symbol)
    """
    line = line.strip()
    if not line or line.startswith('#'):
        return None

    # Try to split into declaration + expected symbol
    # The declaration is always the first quoted string
    m = re.match(r'(".*?::\s*instance")\s*\((\?[^)]+)\)', line)
    if m:
        decl_str = m.group(1)
        expected = m.group(2)
    else:
        # Just the declaration
        m2 = re.match(r'(".*?::\s*instance")', line)
        if not m2:
            return None
        decl_str = m2.group(1)
        expected = None

    type_ast, n = parse_declaration(decl_str)
    got = build_extern_symbol(type_ast, n)
    return decl_str, expected, got


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------

_SELF_TESTS = [
    # primitives
    ('"public: static int StructResolver::Extern<int,15544788>::instance"',
     "?instance@?$Extern@H$0ONDBNE@@StructResolver@@2HA"),
    ('"public: static unsigned short StructResolver::Extern<unsigned short,14627724>::instance"',
     "?instance@?$Extern@G$0NPDDIM@@StructResolver@@2GA"),
    ('"public: static unsigned int StructResolver::Extern<unsigned int,12147028>::instance"',
     "?instance@?$Extern@I$0LJFJFE@@StructResolver@@2IA"),
    ('"public: static unsigned long StructResolver::Extern<unsigned long,15544796>::instance"',
     "?instance@?$Extern@K$0ONDBNM@@StructResolver@@2KA"),
    ('"public: static float StructResolver::Extern<float,12158720>::instance"',
     "?instance@?$Extern@M$0LJIHAA@@StructResolver@@2MA"),
    # 1D arrays
    ('"public: static char * StructResolver::Extern<char [64],15403696>::instance"',
     "?instance@?$Extern@$$BY0EA@D$0OLAKLA@@StructResolver@@2PADA"),
    ('"public: static char * StructResolver::Extern<char [32],15440584>::instance"',
     "?instance@?$Extern@$$BY0CA@D$0OLJKMI@@StructResolver@@2PADA"),
    ('"public: static char * StructResolver::Extern<char [1001],14627831>::instance"',
     "?instance@?$Extern@$$BY0DOJ@D$0NPDDPH@@StructResolver@@2PADA"),
    ('"public: static char * StructResolver::Extern<char [1004],12147576>::instance"',
     "?instance@?$Extern@$$BY0DOM@D$0LJFLHI@@StructResolver@@2PADA"),
    ('"public: static int * StructResolver::Extern<int [9],12147520>::instance"',
     "?instance@?$Extern@$$BY08H$0LJFLEA@@StructResolver@@2PAHA"),
    ('"public: static int * StructResolver::Extern<int [10],12158512>::instance"',
     "?instance@?$Extern@$$BY09H$0LJIGDA@@StructResolver@@2PAHA"),
    ('"public: static int * StructResolver::Extern<int [4],12158496>::instance"',
     "?instance@?$Extern@$$BY03H$0LJIGCA@@StructResolver@@2PAHA"),
    ('"public: static int * StructResolver::Extern<int [100],14635928>::instance"',
     "?instance@?$Extern@$$BY0GE@H$0NPFDJI@@StructResolver@@2PAHA"),
    ('"public: static int * StructResolver::Extern<int [116000],13679120>::instance"',
     "?instance@?$Extern@$$BY0BMFCA@H$0NALKBA@@StructResolver@@2PAHA"),
    ('"public: static int * StructResolver::Extern<int [250],15404616>::instance"',
     "?instance@?$Extern@$$BY0PK@H$0OLAOEI@@StructResolver@@2PAHA"),
    ('"public: static int * StructResolver::Extern<int [21],12147400>::instance"',
     "?instance@?$Extern@$$BY0BF@H$0LJFKMI@@StructResolver@@2PAHA"),
    ('"public: static int * StructResolver::Extern<int [240],14143120>::instance"',
     "?instance@?$Extern@$$BY0PA@H$0NHMOJA@@StructResolver@@2PAHA"),
    ('"public: static wchar_t * StructResolver::Extern<wchar_t [1000],14625656>::instance"',
     "?instance@?$Extern@$$BY0DOI@_W$0NPCLHI@@StructResolver@@2PA_WA"),
    ('"public: static wchar_t * StructResolver::Extern<wchar_t [256],14625144>::instance"',
     "?instance@?$Extern@$$BY0BAA@_W$0NPCJHI@@StructResolver@@2PA_WA"),
    ('"public: static unsigned char * StructResolver::Extern<unsigned char [1024],37762808>::instance"',
     "?instance@?$Extern@$$BY0EAA@E$0CEADGPI@@StructResolver@@2PAEA"),
    ('"public: static unsigned char * StructResolver::Extern<unsigned char [444],12146572>::instance"',
     "?instance@?$Extern@$$BY0BLM@E$0LJFHIM@@StructResolver@@2PAEA"),
    # multi-dim arrays (pointer-to-array form)
    ('"public: static char (* StructResolver::Extern<char [33][1024],15405784>::instance)[1024]"',
     "?instance@?$Extern@$$BY1CB@EAA@D$0OLBCNI@@StructResolver@@2PAY0EAA@DA"),
    ('"public: static short (* StructResolver::Extern<short [33][64][4],14144216>::instance)[64][4]"',
     "?instance@?$Extern@$$BY2CB@EA@3F$0NHNCNI@@StructResolver@@2PAY1EA@3FA"),
    ('"public: static int (* StructResolver::Extern<int [14][169][6],15544800>::instance)[169][6]"',
     "?instance@?$Extern@$$BY2O@KJ@5H$0ONDBOA@@StructResolver@@2PAY1KJ@5HA"),
    ('"public: static int (* StructResolver::Extern<int [48][4],15403816>::instance)[4]"',
     "?instance@?$Extern@$$BY1DA@3H$0OLALCI@@StructResolver@@2PAY03HA"),
    ('"public: static int (* StructResolver::Extern<int [9][10],12158088>::instance)[10]"',
     "?instance@?$Extern@$$BY189H$0LJIEII@@StructResolver@@2PAY09HA"),
    ('"public: static int (* StructResolver::Extern<int [4][7][3],12147048>::instance)[7][3]"',
     "?instance@?$Extern@$$BY2362H$0LJFJGI@@StructResolver@@2PAY162HA"),
    # void *
    ('"public: static void * StructResolver::Extern<void *,5994856>::instance"',
     "?instance@?$Extern@PAX$0FLHJGI@@StructResolver@@2PAXA"),
    # void * [32]
    ('"public: static void * * StructResolver::Extern<void * [32],13214864>::instance"',
     "?instance@?$Extern@$$BY0CA@PAX$0MJKEJA@@StructResolver@@2PAPAXA"),
    # union
    ('"public: static union _LARGE_INTEGER StructResolver::Extern<union _LARGE_INTEGER,14627816>::instance"',
     "?instance@?$Extern@T_LARGE_INTEGER@@$0NPDDOI@@StructResolver@@2T_LARGE_INTEGER@@A"),
    # struct (flat)
    ('"public: static struct _GUID StructResolver::Extern<struct _GUID,14630172>::instance"',
     "?instance@?$Extern@U_GUID@@$0NPDNBM@@StructResolver@@2U_GUID@@A"),
    # struct (scoped)
    ('"public: static struct OpenSHC::AI::AttackInfo::AttackInfoDefinedData StructResolver::Extern<struct OpenSHC::AI::AttackInfo::AttackInfoDefinedData,11847428>::instance"',
     "?instance@?$Extern@UAttackInfoDefinedData@AttackInfo@AI@OpenSHC@@$0LEMHAE@@StructResolver@@2UAttackInfoDefinedData@AttackInfo@AI@OpenSHC@@A"),
    # class (scoped)
    ('"public: static class OpenSHC::UI::Rendering::AlphaAndButtonSurface StructResolver::Extern<class OpenSHC::UI::Rendering::AlphaAndButtonSurface,15910844>::instance"',
     "?instance@?$Extern@VAlphaAndButtonSurface@Rendering@UI@OpenSHC@@$0PCMHLM@@StructResolver@@2VAlphaAndButtonSurface@Rendering@UI@OpenSHC@@A"),
    # pointer to class
    ('"public: static class OpenSHC::UI::MenuView * StructResolver::Extern<class OpenSHC::UI::MenuView *,15544792>::instance"',
     "?instance@?$Extern@PAVMenuView@UI@OpenSHC@@$0ONDBNI@@StructResolver@@2PAVMenuView@UI@OpenSHC@@A"),
    # pointer to pointer to struct
    ('"public: static struct IDirectPlay4 * * StructResolver::Extern<struct IDirectPlay4 * *,14630168>::instance"',
     "?instance@?$Extern@PAPAUIDirectPlay4@@$0NPDNBI@@StructResolver@@2PAPAUIDirectPlay4@@A"),
    # array of struct
    ('"public: static struct OpenSHC::IO::Graphics::ImageHeader * StructResolver::Extern<struct OpenSHC::IO::Graphics::ImageHeader [66000],12158864>::instance"',
     "?instance@?$Extern@$$BY0BABNA@UImageHeader@Graphics@IO@OpenSHC@@$0LJIHJA@@StructResolver@@2PAUImageHeader@Graphics@IO@OpenSHC@@A"),
    ('"public: static struct OpenSHC::Rendering::CreditsRelatedStructure2 * StructResolver::Extern<struct OpenSHC::Rendering::CreditsRelatedStructure2 [288],15440744>::instance"',
     "?instance@?$Extern@$$BY0BCA@UCreditsRelatedStructure2@Rendering@OpenSHC@@$0OLJLGI@@StructResolver@@2PAUCreditsRelatedStructure2@Rendering@OpenSHC@@A"),
    # pointer to class (array)
    ('"public: static struct OpenSHC::Map::Navigation::Algorithms::XYPair * StructResolver::Extern<struct OpenSHC::Map::Navigation::Algorithms::XYPair [21],15541968>::instance"',
     "?instance@?$Extern@$$BY0BF@UXYPair@Algorithms@Navigation@Map@OpenSHC@@$0ONCGNA@@StructResolver@@2PAUXYPair@Algorithms@Navigation@Map@OpenSHC@@A"),
    # SkMasterDataEntry[250]
    ('"public: static struct OpenSHC::IO::SkMasterDataEntry * StructResolver::Extern<struct OpenSHC::IO::SkMasterDataEntry [250],14639696>::instance"',
     "?instance@?$Extern@$$BY0PK@USkMasterDataEntry@IO@OpenSHC@@$0NPGCFA@@StructResolver@@2PAUSkMasterDataEntry@IO@OpenSHC@@A"),
]


def run_self_tests():
    passed = 0
    failed = 0
    for decl_str, expected in _SELF_TESTS:
        try:
            type_ast, n = parse_declaration(decl_str)
            got = build_extern_symbol(type_ast, n)
        except Exception as e:
            print(f"ERROR on: {decl_str}")
            print(f"  {e}")
            failed += 1
            continue
        if got == expected:
            passed += 1
        else:
            print(f"FAIL: {decl_str}")
            print(f"  expected: {expected}")
            print(f"  got:      {got}")
            failed += 1
    print(f"\nSelf-test: {passed}/{passed+failed} passed")
    return failed == 0


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    args = sys.argv[1:]

    if not args:
        ok = run_self_tests()
        sys.exit(0 if ok else 1)

    gen_mode = '--gen' in args
    files = [a for a in args if not a.startswith('--')]

    if not files:
        print("No input file specified.", file=sys.stderr)
        sys.exit(1)

    total = passed = failed = errors = 0

    for path in files:
        with open(path, encoding='utf-8', errors='replace') as f:
            for lineno, raw_line in enumerate(f, 1):
                line = raw_line.strip()
                if not line or line.startswith('#'):
                    continue
                try:
                    result = process_line(line)
                    if result is None:
                        continue
                    decl_str, expected, got = result
                    total += 1
                    if gen_mode or expected is None:
                        print(got)
                    else:
                        if got == expected:
                            passed += 1
                        else:
                            failed += 1
                            print(f"FAIL line {lineno}:")
                            print(f"  decl:     {decl_str}")
                            print(f"  expected: {expected}")
                            print(f"  got:      {got}")
                except Exception as e:
                    errors += 1
                    print(f"ERROR line {lineno}: {e}")
                    print(f"  raw: {line!r}")

    if not gen_mode:
        print(f"\nResults: {passed} passed, {failed} failed, {errors} errors  (total: {total})")
        sys.exit(0 if (failed == 0 and errors == 0) else 1)


if __name__ == "__main__":
    main()