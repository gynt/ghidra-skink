"""
Builds skink's result objects straight from a Ghidra Program, without SARIF.

The objects are the same ones skink would decode from a SARIF export made by
Ghidra's SARIF exporter (sarif.export.*): every field skink declares gets the
value the SARIF writers would have produced for it, and records are produced in
the same order as they appear in a SARIF file. Ordering matters because skink's
database building is order sensitive (overwrites, member detection, dict order).

Not reproduced, because skink never reads them:
  - catch-all `extra` content (comments, stack sizes, flags, ...)
  - `settings` on type infos
  - SARIF sections other than DATATYPE, DEFINED_DATA, FUNCTIONS and SYMBOLS

Requires a started JVM (pyghidra.start()) before import.
"""

from typing import Dict, Generator, List, Tuple

from java.util import Arrays, ArrayList, Comparator  # type: ignore
from jpype import JImplements, JOverride  # type: ignore

from ghidra.program.model.address import GlobalNamespace  # type: ignore
from ghidra.program.model.data import (  # type: ignore
  Array, BitFieldDataType, BuiltInDataType, Composite, DataType,
  Dynamic, Enum, FunctionDefinition, Pointer, Structure, TypeDef,
)
from ghidra.program.database.data import DataTypeUtilities  # type: ignore
from ghidra.program.model.data.ISF import IsfUtilities  # type: ignore
from ghidra.program.model.listing import GhidraClass, Library, Parameter  # type: ignore
from ghidra.program.model.symbol import SourceType, SymbolType  # type: ignore

from skink.sarif.message import Message
from skink.sarif.TypeInfo import TypeInfo
from skink.sarif.symbols.location import Address, Location, PhysicalLocation
from skink.sarif.symbols.symbol import SymbolResult
from skink.sarif.symbols.symbolProperties import AdditionalSymbolProperties, SymbolProperties
from skink.sarif.functions.FunctionResult import FunctionResult
from skink.sarif.functions.FunctionProperties import FunctionProperties
from skink.sarif.functions.AdditionalFunctionProperties import AdditionalFunctionProperties
from skink.sarif.functions.Param import Param
from skink.sarif.functions.RegVar import RegVar
from skink.sarif.functions.Stack import Stack
from skink.sarif.functions.StackVar import StackVar
from skink.sarif.defineddata.DefinedDataResult import DefinedDataResult
from skink.sarif.defineddata.DefinedDataProperties import DefinedDataProperties
from skink.sarif.defineddata.AdditionalDefinedDataProperties import AdditionalDefinedDataProperties
from skink.sarif.datatypes.DataTypeResult import DataTypeResult
from skink.sarif.datatypes.DataTypeProperties import DataTypeProperties
from skink.sarif.datatypes.AdditionalDataTypeProperties import AdditionalDataTypeProperties
from skink.sarif.datatypes.StructField import StructField
from skink.sarif.datatypes.UnionResult import UnionResult, UnionProperties, AdditionalUnionProperties, UnionField
from skink.sarif.datatypes.EnumResult import EnumResult, EnumProperties, AdditionalEnumProperties
from skink.sarif.datatypes.TypedefResult import TypedefResult, TypedefProperties, AdditionalTypedefProperties
from skink.sarif.datatypes.TypedObject import TypedObjectResult, TypedObjectProperties, AdditionalTypedObjectProperties
from skink.sarif.datatypes.FunctionSignatureResult import (
  FunctionSignatureResult, FunctionSignatureProperties, AdditionalFunctionSignatureProperties,
  FunctionSignatureRetTypeInfo, FunctionSignatureParam,
)

from .construct import new as _new
from skink.export.project.project import Record

_DEFAULT = SourceType.DEFAULT
_LABEL = SymbolType.LABEL
_FUNCTION = SymbolType.FUNCTION
_CLASS = SymbolType.CLASS
_LIBRARY = SymbolType.LIBRARY
_NAMESPACE = SymbolType.NAMESPACE


def _location(address: int, length: int) -> Location:
  return _new(Location, physicalLocation=_new(PhysicalLocation, address=_new(Address, absoluteAddress=address, length=length, extra={}), extra={}), extra={})


def _locations(address_set) -> List[Location]:
  # SarifUtils.setLocations(AddressSetView)
  return [_location(int(r.getMinAddress().getOffset()), int(r.getLength())) for r in address_set.getAddressRanges()]


@JImplements(Comparator)
class _StackVarComparator:
  # ExtFunctionStack sorts with this comparator when a function has custom storage.
  # Sorting happens in Java so the (not necessarily consistent) comparator yields the identical order.
  @JOverride
  def compare(self, o1, o2):
    if isinstance(o1, Parameter) and isinstance(o2, Parameter):
      return int(o1.getOrdinal()) - int(o2.getOrdinal())
    return int(o1.getStackOffset()) - int(o2.getStackOffset())

  @JOverride
  def equals(self, other):
    return self is other


class ProgramExtractor(object):

  def __init__(self, program):
    self.program = program
    self.dtm = program.getDataTypeManager()
    self._symbol_cache: Dict[int, SymbolResult] = {}
    self._namespace_cache: Dict[int, Tuple[str, bool]] = {}
    self._chain_cache: Dict[int, List[SymbolResult]] = {}
    self._stack_var_comparator = _StackVarComparator()

  # --- records in SARIF file order ---

  def records(self) -> Generator[Record]:
    """All records skink uses, in the order of a SARIF file written by Ghidra's SarifExporter."""
    yield from self.datatype_records()
    yield from self.defined_data_records()
    yield from self.function_records()
    yield from self.symbol_records()

  # --- SYMBOLS (sarif.export.symbols) ---

  def _namespace_location(self, namespace) -> Tuple[str, bool]:
    """ExtSymbol.getNamespace: ("A::B::", any ancestor is a class)"""
    if namespace.isGlobal():
      return "", False
    key = namespace.getID()
    cached = self._namespace_cache.get(key)
    if cached is None:
      parent_location, parent_is_class = self._namespace_location(namespace.getParentNamespace())
      cached = (f"{parent_location}{namespace.getName()}::", parent_is_class or isinstance(namespace, GhidraClass))
      self._namespace_cache[key] = cached
    return cached

  def _ext_symbol(self, symbol) -> SymbolResult:
    key = symbol.getID()
    sr = self._symbol_cache.get(key)
    if sr is not None:
      return sr
    parent = symbol.getParentNamespace()
    location, namespace_is_class = self._namespace_location(parent)
    symbol_type = symbol.getSymbolType()
    if symbol_type == _CLASS:
      type = "class"
    elif symbol_type == _LIBRARY:
      type = "library"
    elif symbol_type == _NAMESPACE:
      type = "namespace"
    else:
      type = ""
    sr = _new(SymbolResult, 
      message=_new(Message, text="Symbol", extra={}),
      ruleId="SYMBOLS",
      kind="informational",
      level="none",
      locations=[_location(int(symbol.getAddress().getOffset()), 1)],
      properties=_new(SymbolProperties, additionalProperties=_new(AdditionalSymbolProperties, 
        name=symbol.getName(),
        location=location,
        kind="global" if symbol.isGlobal() or isinstance(parent, Library) else "local",
        sourceType=symbol.getSource().toString(),
        primary=symbol.isPrimary(),
        pinned=symbol.isPinned(),
        extra={},
        type=type,
        namespaceIsClass=namespace_is_class,
      ), extra={}),
      extra={},
    )
    self._symbol_cache[key] = sr
    return sr

  def _symbol_with_parents(self, symbol, out: List[SymbolResult]):
    # SarifSymbolWriter.addSymbol / SarifFunctionWriter.addSymbol: parents first
    parent = symbol.getParentNamespace()
    if parent is None:
      return
    if not parent.isGlobal():
      out.extend(self._parent_chain(symbol.getParentSymbol()))
    out.append(self._ext_symbol(symbol))

  def _parent_chain(self, parent_symbol) -> List[SymbolResult]:
    """What _symbol_with_parents emits for a parent symbol, cached since parents are shared a lot."""
    # Keyed by the parent *symbol*: it is not always the parent namespace's symbol
    # (thunks in a library namespace have the global symbol as parent symbol)
    key = parent_symbol.getID()
    chain = self._chain_cache.get(key)
    if chain is None:
      chain = self._chain_cache[key] = []
      self._symbol_with_parents(parent_symbol, chain)
    return chain

  def symbol_records(self) -> Generator[Record]:
    it = self.program.getSymbolTable().getSymbolIterator()
    out: List[SymbolResult] = []
    for symbol in it:
      if symbol.getSource() == _DEFAULT:
        continue
      symbol_type = symbol.getSymbolType()
      if symbol_type != _LABEL and symbol_type != _FUNCTION:
        continue
      self._symbol_with_parents(symbol, out)
      for sr in out:
        yield "SYMBOLS", "Symbol", sr
      out.clear()

  # --- FUNCTIONS (sarif.export.func) ---

  def _ext_datatype(self, dt) -> TypeInfo:
    """ExtDataType: name, location, kind, size"""
    # Not cached by data type: Java equals() considers e.g. builtin and database pointers equal
    return _new(TypeInfo, extra={}, kind=IsfUtilities.getKind(dt), name=dt.getName(),
                location=dt.getCategoryPath().getPath(), size=int(dt.getLength()))

  def _ext_function_param(self, p) -> Param:
    dt = p.getDataType()
    formal_dt = p.getFormalDataType()
    registers = p.getRegisters()
    try:
      stack_offset = int(p.getStackOffset())
    except Exception:  # UnsupportedOperationException for non-stack storage
      stack_offset = -1
    return _new(Param, 
      ordinal=int(p.getOrdinal()),
      size=int(p.getLength()),
      typeName=dt.getName(),
      typeLocation=dt.getCategoryPath().getPath(),
      type=self._ext_datatype(dt),
      formalTypeName=formal_dt.getName(),
      formalTypeLocation=formal_dt.getCategoryPath().getPath(),
      formalType=self._ext_datatype(formal_dt),
      isAutoParameter=p.isAutoParameter(),
      isForcedIndirect=p.isForcedIndirect(),
      stackOffset=stack_offset,
      name=p.getName(),
      location=dt.getCategoryPath().getPath(),
      extra={},
      registers=[r.getName() for r in registers] if registers is not None else [],
    )

  def _ext_function_regvar(self, p) -> RegVar:
    dt = p.getDataType()
    return _new(RegVar, 
      register=p.getRegister().getName(),
      size=int(p.getLength()),
      typeName=dt.getName(),
      typeLocation=dt.getCategoryPath().getPath(),
      type=self._ext_datatype(dt),
      name=p.getName(),
      location=dt.getCategoryPath().getPath(),
      extra={},
    )

  def _ext_function_stack(self, function) -> Stack:
    variables = function.getStackFrame().getStackVariables()
    if function.hasCustomVariableStorage():
      Arrays.sort(variables, self._stack_var_comparator)
    stack_vars = []
    for v in variables:
      dt = v.getDataType()
      stack_vars.append(_new(StackVar, 
        size=int(v.getLength()),
        offset=int(v.getStackOffset()),
        typeName=dt.getName(),
        typeLocation=dt.getCategoryPath().getPath(),
        type=self._ext_datatype(dt),
        name=v.getName(),
        location=dt.getCategoryPath().getPath(),
        extra={},
      ))
    return _new(Stack, stackVars=stack_vars, extra={})

  def _ext_function(self, function) -> FunctionResult:
    # ExtFunction
    name = function.getName() if function.getSymbol().getSource() != _DEFAULT else function.getName(True)
    namespace_object = function.getParentNamespace()
    namespace, namespace_is_class = "", False
    if not isinstance(namespace_object, GlobalNamespace):
      namespace = namespace_object.getName(True)
      namespace_is_class = isinstance(namespace_object, GhidraClass)
    value = function.getPrototypeString(True, True) if function.getSignatureSource() != _DEFAULT else ""
    params, reg_vars = [], []
    for p in function.getParameters():
      if p.isRegisterVariable():
        reg_vars.append(self._ext_function_regvar(p))
      params.append(self._ext_function_param(p))
    return _new(FunctionResult, 
      ruleId="FUNCTIONS",
      locations=_locations(function.getBody()),
      properties=_new(FunctionProperties, additionalProperties=_new(AdditionalFunctionProperties, 
        name=name,
        location=function.getEntryPoint().toString(),
        callingConvention=function.getCallingConventionName(),
        namespaceIsClass=namespace_is_class,
        stack=self._ext_function_stack(function),
        regVars=reg_vars,
        ret=self._ext_function_param(function.getReturn()),
        params=params,
        extra={},
        hasVarArgs=function.hasVarArgs(),
        namespace=namespace,
        value=value,
      ), extra={}),
      extra={},
    )

  def function_records(self) -> Generator[Record]:
    out: List[SymbolResult] = []
    for function in self.program.getListing().getFunctions(self.program.getMemory(), True):
      self._symbol_with_parents(function.getSymbol(), out)
      for sr in out:
        yield "SYMBOLS", "Symbol", sr
      out.clear()
      yield "FUNCTIONS", "Function", self._ext_function(function)

  # --- DEFINED_DATA (sarif.export.dd) ---

  def defined_data_records(self) -> Generator[Record]:
    for data in self.program.getListing().getDefinedData(self.program.getMemory(), True):
      dt = data.getDataType()
      name = dt.getName()
      location = dt.getCategoryPath().getPath()
      start = int(data.getMinAddress().getOffset())
      end = int(data.getMaxAddress().getOffset())
      yield "DEFINED_DATA", "DefinedData", _new(DefinedDataResult, 
        message=_new(Message, text="DefinedData", extra={}),
        ruleId="DEFINED_DATA",
        kind="informational",
        level="none",
        locations=[_location(start, end - start + 1)],
        properties=_new(DefinedDataProperties, additionalProperties=_new(AdditionalDefinedDataProperties, 
          typeName=name,
          typeLocation=location,
          name=name,
          location=location,
          extra={},
        ), extra={}),
        extra={},
      )

  # --- DATATYPE (sarif.export.data, ghidra.program.model.data.ISF) ---

  def datatype_records(self) -> Generator[Record]:
    return _DataTypeExtractor(self.dtm).records()


def _type_info(kind="", name="", location="", size=-1, count=-1, subtype=None, endian="", is_variable_length=False) -> TypeInfo:
  return _new(TypeInfo, extra={}, kind=kind, endian=endian, name=name, location=location, subtype=subtype,
                  size=size, count=count, isVariableLength=is_variable_length)


class _DataTypeExtractor(object):
  """
  Mirrors SarifDataTypeWriter (ExtIsfDataTypeWriter / IsfDataTypeWriter).

  The writer processes all data types sorted by path name. When a typedef refers
  to a (non-builtin, non-pointer) type that the writer already processed, the
  typedef's "type" becomes the SARIF wrapper of that earlier result, which decodes
  as a type info with kind "informational". `self.processed` tracks that state.
  """

  def __init__(self, dtm):
    self.dtm = dtm
    self.processed: set[str] = set()

  def records(self) -> Generator[Record]:
    data_types = ArrayList()
    self.dtm.getAllDataTypes(data_types)
    by_path = {}
    for dt in data_types:
      by_path[dt.getPathName()] = dt
    for path in sorted(by_path.keys()):
      dt = by_path[path]
      if DataTypeUtilities.isConflictDataType(dt):
        continue
      record = self._record(dt)
      self.processed.add(path)
      if record is not None and self._is_written(dt):
        yield record

  @staticmethod
  def _is_written(dt) -> bool:
    # IsfDataTypeWriter.processMap only adds these kinds of data types to the output (no arrays, for example)
    return (isinstance(dt, FunctionDefinition) or IsfUtilities.isBaseDataType(dt) or isinstance(dt, TypeDef)
            or isinstance(dt, Enum) or isinstance(dt, Composite))

  @staticmethod
  def _base_data_type(dt):
    # IsfUtilities.getBaseDataType
    while dt is not None:
      if isinstance(dt, Array) or isinstance(dt, Pointer):
        dt = dt.getDataType()
      elif isinstance(dt, BitFieldDataType):
        dt = dt.getBaseDataType()
      else:
        break
    return dt

  @staticmethod
  def _typed_object_size(dt) -> int:
    return -1 if dt.hasLanguageDependantLength() else int(dt.getLength())

  def _record(self, dt) -> Record | None:
    # getIsfObject + SarifDataType.objToMessage
    if isinstance(dt, Pointer) or isinstance(dt, Array):
      return "DATATYPE", "DT.TypedObject", self._typed_object(dt)
    if isinstance(dt, Dynamic):
      replacement = dt.getReplacementBaseType()
      if replacement is None or replacement.getPathName() in self.processed:
        return None  # nothing, or a wrapper of an earlier result (DT.Base), unused by skink
      return self._record(replacement)
    if isinstance(dt, BuiltInDataType):
      return None  # DT.Builtin, unused by skink
    if isinstance(dt, TypeDef):
      result = self._typedef(dt)
      return None if result is None else ("DATATYPE", "DT.Typedef", result)
    if isinstance(dt, Composite):
      if isinstance(dt, Structure):
        return "DATATYPE", "DT.Struct", self._struct(dt)
      return "DATATYPE", "DT.Union", self._union(dt)
    if isinstance(dt, Enum):
      return "DATATYPE", "DT.Enum", self._enum(dt)
    if isinstance(dt, FunctionDefinition):
      return "DATATYPE", "DT.Function", self._function_definition(dt)
    return None

  # -- type infos as produced by IsfDataTypeWriter.getObjectDataType / getObjectTypeDeclaration --

  def _object_data_type(self, dt) -> TypeInfo:
    if dt is None:
      return _type_info(kind="base", name="void")  # IsfDataTypeNull
    base = self._base_data_type(dt)
    if not dt.equals(base):
      if isinstance(dt, Array):  # IsfDataTypeArray
        return _type_info(kind="array", name=dt.getName(), location=dt.getCategoryPath().getPath(),
                          count=int(dt.getNumElements()), subtype=self._object_data_type(dt.getDataType()))
      if isinstance(dt, BitFieldDataType):  # IsfDataTypeBitField
        return _type_info(kind="bitfield", name=dt.getName(), location=dt.getCategoryPath().getPath())
      # IsfDataTypeTypeDef
      return _type_info(kind=IsfUtilities.getKind(dt), name=dt.getName(), location=dt.getCategoryPath().getPath(),
                        subtype=self._object_data_type(base))
    # IsfDataTypeDefault
    return _type_info(kind=IsfUtilities.getKind(dt), name=dt.getName(), location=dt.getCategoryPath().getPath(),
                      size=int(dt.getLength()))

  def _object_type_declaration(self, component) -> TypeInfo | None:
    dt = component.getDataType()
    if isinstance(dt, Dynamic):
      if dt.canSpecifyLength():
        replacement = dt.getReplacementBaseType()
        if replacement is not None:
          replacement = replacement.clone(self.dtm)
          element_length = int(replacement.getLength())
          if element_length > 0:  # ExtIsfDynamicComponent
            count = (int(component.getLength()) + element_length - 1) // element_length
            return _type_info(kind="array", name=dt.getName(), location=dt.getCategoryPath().getPath(),
                              subtype=self._object_data_type(replacement), count=count, is_variable_length=True)
      return None
    base = self._base_data_type(dt)
    if isinstance(base, FunctionDefinition):  # IsfFunctionPointer
      return _type_info(kind="pointer", name=base.getName(), location=base.getCategoryPath().getPath(),
                        subtype=_type_info(kind="function", name=base.getName(), location=base.getCategoryPath().getPath()))
    return self._object_data_type(dt)

  # -- composites --

  def _components(self, composite, field_class):
    fields = {}
    is_structure = isinstance(composite, Structure)
    for component in composite.getDefinedComponents():
      field_name = component.getFieldName()
      key = field_name
      if key is None:
        key = f"field{int(component.getOrdinal())}"
        if is_structure:
          key += f"_0x{int(component.getOffset()):x}"
      dt = component.getDataType()
      comment = component.getComment()
      kwargs = dict(
        offset=int(component.getOffset()),
        type=self._object_type_declaration(component),
        ordinal=int(component.getOrdinal()),
        length=int(component.getLength()),
        name=dt.getName(),
        location=dt.getCategoryPath().getPath(),
        extra={},
        noFieldName=field_name is None or field_name == "",
      )
      if field_class is StructField:
        fields[key] = _new(StructField, **kwargs, comment=comment if comment is not None else "", field_name=field_name if field_name is not None else "")
      else:
        fields[key] = _new(UnionField, **kwargs, field_name=field_name)
    return fields

  @staticmethod
  def _composite_size(composite) -> int:
    return 0 if composite.isZeroLength() else int(composite.getLength())

  def _struct(self, dt) -> DataTypeResult:
    return _new(DataTypeResult, 
      message=_new(Message, text="DT.Struct", extra={}),
      ruleId="DATATYPE",
      properties=_new(DataTypeProperties, additionalProperties=_new(AdditionalDataTypeProperties, 
        packed="true" if dt.isPackingEnabled() else "false",
        alignment=f"{int(dt.getAlignment()):x}",
        kind="struct",
        size=self._composite_size(dt),
        fields=self._components(dt, StructField),
        name=dt.getName(),
        location=dt.getCategoryPath().getPath(),
        extra={},
      ), extra={}),
      extra={},
    )

  def _union(self, dt) -> UnionResult:
    return _new(UnionResult, 
      message=_new(Message, text="DT.Union", extra={}),
      ruleId="DATATYPE",
      properties=_new(UnionProperties, additionalProperties=_new(AdditionalUnionProperties, 
        name=dt.getName(),
        location=dt.getCategoryPath().getPath(),
        packed="true" if dt.isPackingEnabled() else "false",
        alignment=f"{int(dt.getAlignment()):x}",
        kind="union",
        size=self._composite_size(dt),
        fields=self._components(dt, UnionField),
        extra={},
      ), extra={}),
      extra={},
    )

  # -- enums, function definitions --

  def _enum(self, dt) -> EnumResult:
    return _new(EnumResult, 
      message=_new(Message, text="DT.Enum", extra={}),
      ruleId="DATATYPE",
      properties=_new(EnumProperties, additionalProperties=_new(AdditionalEnumProperties, 
        size=int(dt.getLength()),
        base="int",
        constants={n: int(dt.getValue(n)) for n in dt.getNames()},
        name=dt.getName(),
        location=dt.getCategoryPath().getPath(),
        extra={},
      ), extra={}),
      extra={},
    )

  def _function_definition(self, dt) -> FunctionSignatureResult:
    # ExtIsfFunction
    rt = dt.getReturnType()
    if rt is not None and rt != DataType.DEFAULT:
      ret_type = _new(FunctionSignatureRetTypeInfo, extra={}, kind=IsfUtilities.getKind(rt), name=rt.getName(),
                                              location=rt.getCategoryPath().getPath(), size=int(rt.getLength()))
    else:
      ret_type = _new(FunctionSignatureRetTypeInfo, extra={})
    params = []
    for var in dt.getArguments():
      pdt = var.getDataType()
      params.append(_new(FunctionSignatureParam, 
        # the parameter name gets overwritten by the type name in ExtIsfFunction
        name=pdt.getName() if pdt is not None else var.getName(),
        size=int(var.getLength()),
        ordinal=int(var.getOrdinal()),
        location=pdt.getCategoryPath().getPath() if pdt is not None else None,
        kind=IsfUtilities.getKind(pdt) if pdt is not None else None,
        extra={},
      ))
    description = dt.getDescription()
    return _new(FunctionSignatureResult, 
      ruleId="DATATYPE",
      properties=_new(FunctionSignatureProperties, additionalProperties=_new(AdditionalFunctionSignatureProperties, 
        name=dt.getName(),
        location=dt.getCategoryPath().getPath(),
        kind="function",
        callingConventionName=dt.getCallingConventionName(),
        hasVarArgs=dt.hasVarArgs(),
        hasNoReturn=dt.hasNoReturn(),
        retType=ret_type,
        params=params,
        extra={},
        comment=description if description is not None else "",
      ), extra={}),
      # FunctionSignatureResult has no message field, so it lands in the catch-all
      extra={"message": {"text": "DT.Function"}, "kind": "informational", "level": "none"},
    )

  # -- typedefs and typed objects --

  def _typed_object(self, dt) -> TypedObjectResult:
    # ExtIsfTypedObject with type = getObjectDataType(getBaseDataType(dt))
    base = self._base_data_type(dt)
    type = self._object_data_type(base)
    return _new(TypedObjectResult, 
      message=_new(Message, text="DT.TypedObject", extra={}),
      ruleId="DATATYPE",
      properties=_new(TypedObjectProperties, additionalProperties=_new(AdditionalTypedObjectProperties, 
        type=type,
        kind=IsfUtilities.getKind(dt),
        size=self._typed_object_size(dt),
        name=dt.getName(),
        location=dt.getCategoryPath().getPath(),
        extra={},
        typeLocation=type.location if base is not None else "",
      ), extra={}),
      extra={},
    )

  def _builtin_type_info(self, builtin) -> TypeInfo:
    # IsfBuiltIn
    return _type_info(kind=IsfUtilities.getBuiltInKind(builtin), name=builtin.getName(),
                      location=builtin.getCategoryPath().getPath(), size=int(builtin.getLength()),
                      endian=IsfUtilities.getEndianness(builtin))

  def _pointer_type_info(self, pointer) -> TypeInfo:
    # IsfPointer
    return _type_info(kind="pointer", size=self._typed_object_size(pointer), endian=IsfUtilities.getEndianness(pointer))

  def _typedef(self, dt) -> TypedefResult | None:
    # IsfDataTypeWriter.getObjectTypeDef with the Ext* variants
    base = dt.getDataType()
    name = dt.getName()
    location = dt.getCategoryPath().getPath()
    if isinstance(base, BuiltInDataType):  # ExtIsfTypedefBase
      properties = _new(AdditionalTypedefProperties, 
        type=self._builtin_type_info(base), kind="typedef", size=int(dt.getLength()), name=name, location=location,
        extra={}, endian=IsfUtilities.getEndianness(dt))
    elif not isinstance(base, Pointer):  # ExtIsfTypedefUser
      properties = _new(AdditionalTypedefProperties, 
        type=self._nested_type_info(base), kind="typedef", size=int(dt.getLength()), name=name, location=location,
        extra={}, typeName=base.getName(), typeLocation=base.getCategoryPath().getPath())
    else:  # ExtIsfTypedefPointer
      pointer = dt.getBaseDataType()
      properties = _new(AdditionalTypedefProperties, 
        type=self._pointer_type_info(pointer), kind="typedef", size=self._typed_object_size(pointer), name=name,
        location=location, extra={}, endian=IsfUtilities.getEndianness(pointer),
        typeName=base.getName(), typeLocation=base.getCategoryPath().getPath())
    return _new(TypedefResult, 
      message=_new(Message, text="DT.Typedef", extra={}),
      ruleId="DATATYPE",
      properties=_new(TypedefProperties, additionalProperties=properties, extra={}),
      extra={},
    )

  def _nested_type_info(self, dt) -> TypeInfo | None:
    """The type info of getIsfObject(dt) when it is nested in a typedef."""
    if isinstance(dt, Pointer) or isinstance(dt, Array):  # ExtIsfTypedObject
      return _type_info(kind=IsfUtilities.getKind(dt), name=dt.getName(), location=dt.getCategoryPath().getPath(),
                        size=self._typed_object_size(dt))
    if dt.getPathName() in self.processed:
      return _type_info(kind="informational")  # SarifDataType wrapper of the earlier result
    if isinstance(dt, Dynamic):
      replacement = dt.getReplacementBaseType()
      return None if replacement is None else self._nested_type_info(replacement)
    if isinstance(dt, BuiltInDataType):  # IsfBuiltIn
      return self._builtin_type_info(dt)
    name = dt.getName()
    location = dt.getCategoryPath().getPath()
    if isinstance(dt, TypeDef):
      base = dt.getDataType()
      if isinstance(base, BuiltInDataType):  # ExtIsfTypedefBase
        return _type_info(kind="typedef", name=name, location=location, size=int(dt.getLength()),
                          endian=IsfUtilities.getEndianness(dt))
      if not isinstance(base, Pointer):  # ExtIsfTypedefUser
        return _type_info(kind="typedef", name=name, location=location, size=int(dt.getLength()))
      pointer = dt.getBaseDataType()  # ExtIsfTypedefPointer
      return _type_info(kind="typedef", name=name, location=location, size=self._typed_object_size(pointer),
                        endian=IsfUtilities.getEndianness(pointer))
    if isinstance(dt, Composite):  # ExtIsfComposite
      return _type_info(kind="struct" if isinstance(dt, Structure) else "union", name=name, location=location,
                        size=self._composite_size(dt))
    if isinstance(dt, Enum):  # IsfEnum has no kind
      return _type_info(name=name, location=location, size=int(dt.getLength()))
    if isinstance(dt, FunctionDefinition):  # ExtIsfFunction
      return _type_info(kind="function", name=name, location=location)
    return None
