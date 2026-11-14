from skink.sarif.TypeInfo import TypeInfo
from skink.sarif.functions.Param import Param
from skink.sarif.datatypes.UnionResult import UnionField
from skink.sarif.symbols.symbolProperties import AdditionalSymbolProperties

from skink.ghidra.construct import new


def test_defaults_match_dataclass_init():
  assert new(TypeInfo, extra={}) == TypeInfo(extra={})
  assert new(TypeInfo, extra={}, kind="array", count=3) == TypeInfo(extra={}, kind="array", count=3)
  assert new(UnionField, name="n", location="/", length=4, ordinal=0, offset=0, type=None, extra={}) == \
    UnionField(name="n", location="/", length=4, ordinal=0, offset=0, type=None, extra={})


def test_all_fields_present():
  obj = new(AdditionalSymbolProperties, name="x", location="", kind="global", sourceType="USER_DEFINED",
            primary=True, pinned=False, extra={})
  assert obj.type == "" and obj.namespaceIsClass is False
  assert repr(obj) == repr(AdditionalSymbolProperties(name="x", location="", kind="global", sourceType="USER_DEFINED",
                                                      primary=True, pinned=False, extra={}))


def test_default_factory_not_shared():
  kwargs = dict(ordinal=0, size=4, typeName="int", typeLocation="/", type=None, formalTypeName="int",
                formalTypeLocation="/", formalType=None, isAutoParameter=False, isForcedIndirect=False,
                stackOffset=4, name="a", location="/", extra={})
  a = new(Param, **kwargs)
  b = new(Param, **kwargs)
  assert a.registers == [] and a.registers is not b.registers
  assert a == Param(**kwargs)
