from jinja2 import Environment, FileSystemLoader
from importlib.resources import path

from collections.abc import Callable
from typing import Collection
from skink.architecture.functionsignatures import FunctionSignature
from skink.architecture.namespaces.namespace import Namespace
from skink.architecture.functions.function import Function
from skink.export.enums.enumfamilies import SUFFICES
from skink.export.types import remap_type
from skink.sarif.BasicResult import BasicResult
from skink.sarif.datatypes.EnumResult import EnumResult
from skink.sarif.datatypes.BasicDataTypeResult import BasicDataTypeResult
from skink.sarif.defineddata.DefinedDataResult import DefinedDataResult
from skink.sarif.symbols.symbol import SymbolResult
from skink.sarif.functions.FunctionResult import FunctionResult
from skink.architecture.classes.cls import Class
from skink.architecture.structs.struct import Struct
from skink.architecture.unions.union import Union
from skink.architecture.typedefs import Typedef
from skink.architecture.enums import Enum
from skink.export.project.exportcontents import ExportContents
from skink.utils.OrderedSet import OrderedSet
from skink.export.context import DEFAULT, Context, FileRules, TransformationRules
from skink.architecture.common.sanitization import sanitize_calling_convention, sanitize_name
from skink.architecture.common.includes import includes_for_type_name_location
from skink.export.location import transform_location
from skink.export.mangler import *
from skink.export.mangler import _parse_type
from skink.export.util import *
from skink.export.mangler.typedefs import COMMON as TYPEDEFS_COMMON

from typing import Dict, List, Iterable, Tuple, Any

from dataclasses import dataclass
from dataclasses_json import dataclass_json
import re

DEFAULT_TEMPLATE_PATH = "skink.export.styles.style3.templates"
EXPORT_SETTINGS_CLASS_INCLUDE: Context = DEFAULT.copy() # type: ignore
EXPORT_SETTINGS_CLASS_INCLUDE.include.functions_this_parameter_type = False
EXPORT_SETTINGS_CLASS_INCLUDE.include.prefix_include = False
EXPORT_SETTINGS_CLASS_INCLUDE.include.file_extension = ".hpp"

EXPORT_SETTINGS_CLASS_INCLUDE.struct_rules.field_eol_char = False
EXPORT_SETTINGS_CLASS_INCLUDE.struct_rules.suffix = ""

EXPORT_SETTINGS_CLASS_INCLUDE.class_rules.export_constructor = False
EXPORT_SETTINGS_CLASS_INCLUDE.class_rules.suffix = ""
EXPORT_SETTINGS_CLASS_INCLUDE.class_rules.class_as_namespace = False

# EXPORT_SETTINGS_CLASS_SHIM_FILENAME: Context = DEFAULT.copy() # type: ignore
# EXPORT_SETTINGS_CLASS_SHIM_FILENAME.class_rules.suffix = "_"


@dataclass
class BinaryContext:
  hash: str = "HASH"
  abbreviation: str = "ABBREV"
  reccmp_binary: str = "BIN"


DEFAULT_BINARY_CONTEXT: BinaryContext = BinaryContext()

class Exporter(object):
  
  def __init__(self, template_path: str = DEFAULT_TEMPLATE_PATH, binary_context: BinaryContext = DEFAULT_BINARY_CONTEXT,
               transformation_rules: TransformationRules = TransformationRules(), file_rules = FileRules(),
               expose_original_methods: bool = False, includes_remapping: List[Tuple[str, str]] = [],
               includes_exclude_regex: List[str] = [],
               type_mapping: Dict[Tuple[str, str], Tuple[str, str]] = {},
               inject_forwards_in_files: Dict[str, List[Tuple[str, str]]] = {},
               exclude_files_regex: List[str] = [],
               inject_includes_in_files: Dict[str, List[str]] = {}):
    self.template_path = template_path
    self.binary_context = binary_context
    # self.transformation_rules = transformation_rules
    self.esci: Context = EXPORT_SETTINGS_CLASS_INCLUDE.copy() # type: ignore
    self.esci.location_rules.transformation_rules = transformation_rules.copy() # type: ignore
    self.esci.include.remap += includes_remapping
    self.esci.include.exclude += includes_exclude_regex
    self.esci.include.exclude_use_regex = True
    for old, new in type_mapping.items():
      self.esci.type_rules.type_mapping[old] = new
    # self.escsf: Context = EXPORT_SETTINGS_CLASS_SHIM_FILENAME.copy() # type: ignore
    # self.escsf.location_rules.transformation_rules = transformation_rules.copy() # type: ignore
    self.expose_original_methods = expose_original_methods
    self.inject_forwards_in_files = inject_forwards_in_files
    self.exclude_files_regex: List[re.Pattern] = [re.compile(excl) for excl in exclude_files_regex]
    self.inject_includes_in_files = inject_includes_in_files

  def export_addresses(self, objects: Iterable[BasicResult], ignore_switch_data = True, filter_labelled = False, include_address = lambda addr: True):
    if self.template_path != DEFAULT_TEMPLATE_PATH:
      raise Exception()
    anchor, *names = self.template_path.split(".")
    with path(anchor, *names) as p:
      env = Environment(loader=FileSystemLoader(str(p)))
      template = env.get_template("AddressesH.j2")

      addrs: Dict[int, List[str]] = {}
      
      for obj in objects:
        ruleId = obj.ruleId
        if ruleId == "DEFINED_DATA":
          for l in obj.locations:
            addr = l.physicalLocation.address.absoluteAddress
            if addr == 0 or (include_address and not include_address(addr)):
              continue
            name = obj.properties.additionalProperties.name
            location = transform_location(obj.properties.additionalProperties.location.replace("::", "/"), self.esci)
            if location != "/" and location.endswith("/"):
              location = location[:-1]
            if addr not in addrs:
              addrs[addr] = []
            comment = f"type: {location}/{name}"
            if not comment in addrs[addr]:
              addrs[addr].append(comment)
        elif ruleId == "SYMBOLS":
          for l in obj.locations:
            addr = l.physicalLocation.address.absoluteAddress
            if addr == 0 or (include_address and not include_address(addr)):
              continue
            name = obj.properties.additionalProperties.name
            location = transform_location(obj.properties.additionalProperties.location.replace("::", "/"), self.esci)
            if location.endswith("/"):
              location = location[:-1]
            if ignore_switch_data and (name.startswith("switch") or location.startswith("switch") or name.startswith("case_")):
              continue
            if addr not in addrs:
              addrs[addr] = []
            comment = f"label: {name}"
            if not comment in addrs[addr]:
              addrs[addr].append(comment)
            comment = f"location: {location}"
            if not comment in addrs[addr]:
              addrs[addr].append(comment)
        elif ruleId == "FUNCTIONS":
          for l in obj.locations:
            addr = l.physicalLocation.address.absoluteAddress
            if addr == 0 or (include_address and not include_address(addr)):
              continue
            name = obj.properties.additionalProperties.name
            #if ignore_switch_data and (name.startswith("switch")):
              #continue
            if addr not in addrs:
              addrs[addr] = []
            comment = f"type: function"
            if not comment in addrs[addr]:
              addrs[addr].append(comment)

      entries = [{"address": addr, "comments": sorted(comments)} for addr, comments in addrs.items() if len(comments) > 0]
      if filter_labelled:
        entries = [entry for entry in entries if entry["comments"][0].startswith("label: ")]
      entries = sorted(entries, key=lambda entry: entry["address"])
      
      return ExportContents(path=f"precomp/addresses-{self.binary_context.abbreviation}-{self.binary_context.hash}.hpp",
                            contents=template.render({
                              "context": self.binary_context,
                              "addresses": entries,
                              "use_pch": False,
                            }),
                            no_touch=True)

  def _inject_includes(self, includes: Collection[str], path: str):
    if path in self.inject_includes_in_files:
      for include in self.inject_includes_in_files[path]:
        if include:
          if include not in includes:
            yield include


  def export_class_header(self, c: Class):
    if self.template_path != DEFAULT_TEMPLATE_PATH:
      raise Exception()
    anchor, *names = self.template_path.split(".")
    with path(anchor, *names) as p:
      env = Environment(loader=FileSystemLoader(str(p)))
      template = env.get_template("ClassH.j2")

      if not c.structure:
        raise Exception(f"no structure for class {c.namespace()}, which could mean struct and class are in a different namespace")
      
      dstfolder = f"{c.location(ctx=self.esci)}"      
      dst = f"{dstfolder}/{c.name}.hpp"      
      namespace = c.namespace(ctx=self.esci)

      includes = OrderedSet[str]()
      if dst in self.inject_forwards_in_files:
        for forwards, _ in self.inject_forwards_in_files[dst]:
          includes.append(forwards)
      includes += self._inject_includes(includes, dst)
      includes += c.structure.includes(self.esci)
      for m in c.functions(self.esci):
        includes += list(m.includes(self.esci))
      if c.constructor:
        includes += list(c.constructor.includes(self.esci))

      while dst in includes:
        includes.remove(dst)

      usings = includes.copy()
      if dst in self.inject_forwards_in_files:
        for forwards, _ in self.inject_forwards_in_files[dst]:
          usings.remove(forwards)

      methods = [{
        "returnType": f.return_type(ctx=self.esci)[0], 
        "name": sanitize_name(f.name.split("::")[-1]), # split if necessary (mistake in export)
        "parameters": [f"{type_name} {sanitize_name(name)}" for type_name, name in f.parameters(ctx=self.esci)] + (["..."] * f.has_varargs()),
        "address": f.f.locations[0].physicalLocation.address.absoluteAddress,
      } for f in c.functions(self.esci)]

      fields =  list({"string": s, "offset": o, "length": l} for s, o, l in c.structure.export_field_declarations_with_offsets_and_lengths(self.esci))

      contents = template.render({
        "use_pch": False,
        "include_paths": sorted(includes),
        "using_paths": usings,
        "namespace_path": namespace,
        "class_name": f"{c.name}",
        "struct_name": f"{c.name}",
        "fields": fields,
        "class_size": c.structure.s.properties.additionalProperties.size,
        "methods": methods,
        "constructor": {
          "returnType": c.constructor.f.properties.additionalProperties.ret.typeName, 
          "name": sanitize_name(c.constructor.name.split("::")[-1]), # split if necessary (mistake in export)
          "parameters": [f"{param.typeName} {sanitize_name(param.name)}" for param in c.constructor.f.properties.additionalProperties.params if param.name != "this"],
        } if c.constructor else None,
        "expose_original_methods": self.expose_original_methods,
        "is_singleton": c.singleton != None,
        "singleton_name": f"DAT_{c.name}", # TODO: probably almost always correct?
        "singleton_address": c.singleton.defined_data.address() if c.singleton else 0,
        "context": self.binary_context,
        "ifdef_expose_original": self.esci.macro_rules.ifdef_expose_original,
      })

      return ExportContents(path=dst, contents=contents)
  
  def export_class_body(self, c: Class):
    if self.template_path != DEFAULT_TEMPLATE_PATH:
      raise Exception()
    anchor, *names = self.template_path.split(".")
    with path(anchor, *names) as p:
      env = Environment(loader=FileSystemLoader(str(p)))
      template = env.get_template("ClassCPP.j2")


      if not c.structure:
        raise Exception()
      
      includes = OrderedSet[str]()
      for m in c.functions(self.esci):
        includes += list(m.includes(self.esci))
      dst = f"{c.location(ctx=self.esci)}/{c.name}.cpp"
      includes += self._inject_includes(includes, dst)

      methods = [{
        "returnType": f.return_type(ctx=self.esci)[0], 
        "name": sanitize_name(f.name.split("::")[-1]), # split if necessary (mistake in export)
        "parameters": [f"{type_name} {sanitize_name(name)}" for type_name, name in f.parameters(ctx=self.esci)] + (["..."] * f.has_varargs()),
        "parameter_names": [f"{sanitize_name(name)}" for type_name, name in f.parameters(ctx=self.esci)] + (["..."] * f.has_varargs()),
        "address": f.f.locations[0].physicalLocation.address.absoluteAddress,
      } for f in c.functions(self.esci)]

      contents = template.render({
        "context": self.binary_context,
        "include_paths": sorted(includes) + [f"{c.location(ctx=self.esci)}/{c.name}.hpp"],
        "using_paths": sorted(includes),
        "namespace_path": c.namespace(ctx=self.esci),
        "class_name": f"{c.name}",
        "class_size": c.structure.s.properties.additionalProperties.size,
        "methods": methods,
      })

      return ExportContents(path=dst, contents=contents, no_touch=False)
  
  def export_class_body_method(self, c: Class, f: Function):
    if self.template_path != DEFAULT_TEMPLATE_PATH:
      raise Exception()
    anchor, *names = self.template_path.split(".")
    with path(anchor, *names) as p:
      env = Environment(loader=FileSystemLoader(str(p)))
      template = env.get_template("ClassCPP.j2")


      if not c.structure:
        raise Exception()
      
      includes = OrderedSet[str]()
      includes += list(f.includes(self.esci))

      dst = f"{c.location(ctx=self.esci)}/{c.name}/{sanitize_name(f_fixed_name)}.cpp"
      includes += self._inject_includes(includes, dst)

      f_fixed_name = f.name.split("::")[-1]

      methods = [{
        "returnType": f.return_type(ctx=self.esci)[0], 
        "name": sanitize_name(f.name.split("::")[-1]), # split if necessary (mistake in export)
        "parameters": [f"{type_name} {sanitize_name(name)}" for type_name, name in f.parameters(ctx=self.esci)],
        "parameter_names": [f"{sanitize_name(name)}" for type_name, name in f.parameters(ctx=self.esci)],
        "address": f.f.locations[0].physicalLocation.address.absoluteAddress,
      }]

      contents = template.render({
        "context": self.binary_context,
        "include_paths": sorted(includes) + [f"{c.location(ctx=self.esci)}/{c.name}.hpp"],
        "using_paths": sorted(includes),
        "namespace_path": c.namespace(ctx=self.esci),
        "class_name": f"{c.name}",
        "class_size": c.structure.s.properties.additionalProperties.size,
        "methods": methods,
      })

      return ExportContents(path=dst, contents=contents, no_touch=False)
   
  def export_class_header_funcfile(self, c: Class):
    if self.template_path != DEFAULT_TEMPLATE_PATH:
      raise Exception()
    anchor, *names = self.template_path.split(".")
    with path(anchor, *names) as p:
      env = Environment(loader=FileSystemLoader(str(p)))
      template = env.get_template("ClassFunc.j2")


      if not c.structure:
        raise Exception()
      
      includes = OrderedSet[str]()
      for m in c.functions(self.esci):
        includes += list(m.includes(self.esci))

      dst = f"{c.location(ctx=self.esci)}/{c.name}.func.hpp"
      includes += self._inject_includes(includes, dst)
      

      methods = [{
        "returnType": f.return_type(ctx=self.esci)[0], 
        "name": sanitize_name(f.name.split("::")[-1]), # split if necessary (mistake in export)
        "parameters": [f"{type_name} {sanitize_name(name)}" for type_name, name in f.parameters(ctx=self.esci)] + (["..."] * f.has_varargs()),
        "parameter_names": [f"{sanitize_name(name)}" for type_name, name in f.parameters(ctx=self.esci)],
        "parameter_types": [f"{type_name}" for type_name, name in f.parameters(ctx=self.esci)] + (["..."] * f.has_varargs()),
        "address": f.f.locations[0].physicalLocation.address.absoluteAddress,
      } for f in c.functions(self.esci)]

      contents = template.render({
        "context": self.binary_context,
        "include_paths": sorted(includes) + [f"{c.location(ctx=self.esci)}/{c.name}.hpp"],
        "using_paths": sorted(includes),
        "namespace_path": f"{c.structure.namespace(ctx=self.esci)}::{c.name}_Func",
        "class_name": f"{c.name}",
        "class_size": c.structure.s.properties.additionalProperties.size,
        "methods": methods,
      })

      return ExportContents(path=dst, contents=contents, no_touch=False)

  def is_excluded_file(self, path: str):
    for excl in self.exclude_files_regex:
      if excl.search(path):
        return True
    return False

  def export_class(self, c: Class, export_bodies: bool = True) -> List[ExportContents]:
    dst = f"{c.location(ctx=self.esci)}/{c.name}.hpp"
    if self.is_excluded_file(dst):
      return []
    forwards = []
    if dst in self.inject_forwards_in_files:
      for forward_path, contents in self.inject_forwards_in_files[dst]:
        forwards.append(ExportContents(path=forward_path, contents = contents, no_touch = True))

    if not export_bodies:
      return [
        self.export_class_header(c),
        self.export_class_header_funcfile(c),
      ] + forwards
    if self.esci.file_rules.one_file_per_method:
      return [
        self.export_class_header(c),
        self.export_class_header_funcfile(c),
        *[self.export_class_body_method(c, f) for f in c.functions(self.esci)],
      ] + forwards
    return [
      self.export_class_header(c),
      self.export_class_header_funcfile(c),
      self.export_class_body(c),
    ] + forwards
    
  def export_struct(self, s: Struct):
    if self.template_path != DEFAULT_TEMPLATE_PATH:
      raise Exception()
    dst = f"{s.location(ctx=self.esci)}/{s.name}.hpp"
    if self.is_excluded_file(dst):
      return None
    anchor, *names = self.template_path.split(".")
    with path(anchor, *names) as p:
      env = Environment(loader=FileSystemLoader(str(p)))
      template = env.get_template("StructH.j2")

      includes = OrderedSet(s.includes(self.esci))
      includes += self._inject_includes(includes, dst)

      fields =  list({"string": s, "offset": o, "length": l} for s, o, l in s.export_field_declarations_with_offsets_and_lengths(self.esci))
      
      contents = template.render({
        "use_pch": False,
        "include_paths": sorted(includes),
        "using_paths": sorted(includes),
        "namespace_path": s.namespace(ctx=self.esci),
        "struct_name": sanitize_name(s.name),
        "struct_size": s.s.properties.additionalProperties.size,
        "fields": fields,
      })
    
      return ExportContents(path=dst, contents=contents)

  def export_struct_singleton(self, s: Struct):
    if self.template_path != DEFAULT_TEMPLATE_PATH:
      raise Exception()
    anchor, *names = self.template_path.split(".")
    with path(anchor, *names) as p:
      env = Environment(loader=FileSystemLoader(str(p)))
      template = env.get_template("StructH.j2")

      includes = OrderedSet(s.includes(self.esci))

      dst = f"{s.location(ctx=self.esci)}/{s.name}.hpp"
      includes += self._inject_includes(includes, dst)

      fields =  list({"string": s, "offset": o, "length": l} for s, o, l in s.export_field_declarations_with_offsets_and_lengths(self.esci))
      
      contents = template.render({
        "use_pch": False,
        "include_paths": sorted(includes),
        "using_paths": sorted(includes),
        "namespace_path": s.namespace(ctx=self.esci),
        "struct_name": sanitize_name(s.name),
        "struct_size": s.s.properties.additionalProperties.size,
        "fields": fields,
        "is_singleton": True,
        "singleton_name": f"DAT_{s.name}", # TODO: probably almost always correct?
        "singleton_address": s.singleton.defined_data.address() if s.singleton else 0,
        "context": self.binary_context,
        "ifdef_expose_original": self.esci.macro_rules.ifdef_expose_original,
      })
    
      return ExportContents(path=dst, contents=contents)


  def export_union(self, u: Union):
    if self.template_path != DEFAULT_TEMPLATE_PATH:
      raise Exception()
    dst = f"{u.location(ctx=self.esci)}/{u.name}.hpp"
    if self.is_excluded_file(dst):
      return
    anchor, *names = self.template_path.split(".")
    with path(anchor, *names) as p:
      env = Environment(loader=FileSystemLoader(str(p)))
      template = env.get_template("UnionH.j2")

      includes = OrderedSet(u.includes(self.esci))

      includes += self._inject_includes(includes, dst)

      fields =  list({"string": s, "offset": o, "length": l} for s, o, l in u.export_field_declarations_with_offsets_and_lengths(self.esci))
      
      contents = template.render({
        "use_pch": False,
        "include_paths": sorted(includes),
        "using_paths": sorted(includes),
        "namespace_path": u.namespace(ctx=self.esci),
        "union_name": sanitize_name(u.name),
        "union_size": u.s.properties.additionalProperties.size,
        "fields": fields,
      })
    
      return ExportContents(path=dst, contents=contents)

  def export_enum(self, e: Enum, hexvalue: bool = False):
    if self.template_path != DEFAULT_TEMPLATE_PATH:
      raise Exception()
    dst = f"{e.location(ctx=self.esci)}/{e.name}.hpp"
    if self.is_excluded_file(dst):
      return
    anchor, *names = self.template_path.split(".")
    with path(anchor, *names) as p:
      env = Environment(loader=FileSystemLoader(str(p)))
      template1 = env.get_template("EnumH.j2")

      namespace_path = e.namespace(ctx=self.esci)

      fields = [{"name": sanitize_name(key), "value": value} for key, value in e.er.properties.additionalProperties.constants.items()]
      name = e.er.properties.additionalProperties.name
      type = e.er.properties.additionalProperties.base
      contents = template1.render({
        "use_pch": False,
        "namespace_path": namespace_path,
        "name": sanitize_name(name),
        "type": type,
        "fields": fields,
        "hexvalue": hexvalue,
      })
      return ExportContents(path=dst, contents=contents)

  def export_enum_typedef(self, e: Enum):
    if self.template_path != DEFAULT_TEMPLATE_PATH:
      raise Exception()
    dst = f"{e.location(ctx=self.esci)}/{e.name}.hpp"
    if self.is_excluded_file(dst):
      return
    anchor, *names = self.template_path.split(".")
    with path(anchor, *names) as p:
      env = Environment(loader=FileSystemLoader(str(p)))
      template1 = env.get_template("EnumTypedefH.j2")

      namespace_path = e.namespace(ctx=self.esci)
      loc = f"{e.location(ctx=self.esci)}/{e.name}"
      refloc = loc
      for ending in SUFFICES:
        if loc.endswith(ending):
          refloc = loc[:-len(ending)]
          break
      includes = [f"{refloc}.hpp"] # not necessary!
      includes += self._inject_includes(includes, dst)

      name = e.er.properties.additionalProperties.name
      size = e.er.properties.additionalProperties.size
      type_size = -1
      type = "int"
      if size == 4:
        type = "int"
        type_size = 4
      elif size == 2:
        type = "short"
        type_size = 2
      elif size == 1:
        type = "byte"
        type_size = 1
      contents = template1.render({
        "include_paths": includes,
        "use_pch": False,
        "namespace_path": namespace_path,
        "name": sanitize_name(name),
        "type": type,
        "type_size": type_size,
      })
      return ExportContents(path=dst, contents=contents)

  def export_sized_enum(self, e: Enum) -> List[ExportContents]:
    if self.template_path != DEFAULT_TEMPLATE_PATH:
      raise Exception()
    anchor, *names = self.template_path.split(".")
    with path(anchor, *names) as p:
      env = Environment(loader=FileSystemLoader(str(p)))
      template1 = env.get_template("SizedEnum_CPP03_H.j2")

      namespace_path = e.namespace(ctx=self.esci)

      fields = [{"name": sanitize_name(key), "value": value} for key, value in e.er.properties.additionalProperties.constants.items()]
      name = e.er.properties.additionalProperties.name
      type = e.er.properties.additionalProperties.base
      size = e.er.properties.additionalProperties.size
      if size == 2:
        type = "short"
      elif size == 1:
        type = "char"
      path1 = f"{e.location(ctx=self.esci)}/{e.name}.hpp"
      contents1 = template1.render({
        "use_pch": False,
        "namespace_path": namespace_path,
        "name": sanitize_name(name),
        "type": type,
        "fields": fields,
        "size": size
      })

      return [ExportContents(path=path1, contents=contents1)]
    
  def export_function_signature(self, fs: FunctionSignature):
    if self.template_path != DEFAULT_TEMPLATE_PATH:
      raise Exception()
    dst = f"{fs.location(ctx=self.esci)}/{fs.name}.hpp"
    if self.is_excluded_file(dst):
      return
    anchor, *names = self.template_path.split(".")
    with path(anchor, *names) as p:
      env = Environment(loader=FileSystemLoader(str(p)))
      template1 = env.get_template("FunctionSignatureH.j2")

      namespace_path = fs.namespace(ctx=self.esci)
      include_paths: OrderedSet[str] = OrderedSet[str]()
      include_paths += fs.includes(ctx=self.esci)

      include_paths += self._inject_includes(include_paths, dst)
      
      returnTypeName, returnTypeLocation = fs.return_type(ctx=self.esci)
      callingConvention = sanitize_calling_convention(fs.fsr.properties.additionalProperties.callingConventionName)

      # Function signature parameter names are the types...
      parameters = [f"{type_name} " for type_name, type_loc in fs.parameter_types(ctx=self.esci)]
      name = fs.fsr.properties.additionalProperties.name
      contents = template1.render({
        "include_paths": sorted(include_paths),
        "using_paths": sorted(include_paths),
        "use_pch": False,
        "namespace_path": namespace_path,
        "name": sanitize_name(name),
        "parameters": parameters,
        "returnTypeName": returnTypeName,
        "returnTypeLocation": returnTypeLocation,
        "callingConvention": callingConvention,
        # "type": type,
      })
      return ExportContents(path=dst, contents=contents)

  def export_typedef_raw(self, location, name, type, namespace_path, include_paths = [], using_paths = [], use_pch = False):
    if self.template_path != DEFAULT_TEMPLATE_PATH:
      raise Exception()
    dst = f"{location}/{name}.hpp"
    if self.is_excluded_file(dst):
      return
    anchor, *names = self.template_path.split(".")
    with path(anchor, *names) as p:
      env = Environment(loader=FileSystemLoader(str(p)))
      template1 = env.get_template("TypedefH.j2")
      contents = template1.render({
        "include_paths": sorted(include_paths),
        "using_paths": sorted(include_paths),
        "use_pch": False,
        "namespace_path": namespace_path,
        "name": sanitize_name(name),
        "type": type,
        # "returnTypeLocation": typeLocation,
        # "type": type,
      })
      return ExportContents(path=dst, contents=contents)

  def export_typedef(self, td: Typedef):
    if self.template_path != DEFAULT_TEMPLATE_PATH:
      raise Exception()
    dst = f"{td.location(ctx=self.esci)}/{td.name}.hpp"
    if self.is_excluded_file(dst):
      return
    anchor, *names = self.template_path.split(".")
    with path(anchor, *names) as p:
      env = Environment(loader=FileSystemLoader(str(p)))
      template1 = env.get_template("TypedefH.j2")

      namespace_path = td.namespace(ctx=self.esci)
      include_paths: OrderedSet[str] = OrderedSet[str]()
      include_paths += td.includes(ctx=self.esci)

      include_paths += self._inject_includes(include_paths, dst)
      
      typeName, typeLocation = td.type(ctx=self.esci)

      name = td.tr.properties.additionalProperties.name
      contents = template1.render({
        "include_paths": sorted(include_paths),
        "using_paths": sorted(include_paths),
        "use_pch": False,
        "namespace_path": namespace_path,
        "name": sanitize_name(name),
        "type": typeName,
        # "returnTypeLocation": typeLocation,
        # "type": type,
      })
      return ExportContents(path=dst, contents=contents)
  
  def export_namespaced_functions_header(self, ns: Namespace):
    if self.template_path != DEFAULT_TEMPLATE_PATH:
      raise Exception()
    anchor, *names = self.template_path.split(".")
    with path(anchor, *names) as p:
      env = Environment(loader=FileSystemLoader(str(p)))
      template = env.get_template("NamespaceH.j2")

      dst = f"{ns.location(ctx=self.esci)}.hpp"

      includes = OrderedSet[str]()
      for f in ns.functions:
        includes += list(f.includes(self.esci))
      
      includes += self._inject_includes(includes, dst)

      functions = [{
        "returnType": f.return_type(ctx=self.esci)[0], 
        "name": sanitize_name(f.name.split("::")[-1]), # split if necessary (mistake in export)
        "parameters": [f"{type_name} {sanitize_name(name)}" for type_name, name in f.parameters(ctx=self.esci)] + (["..."] * f.has_varargs()),
        "callingConvention": sanitize_calling_convention(f.f.properties.additionalProperties.callingConvention),
        "address": f.f.locations[0].physicalLocation.address.absoluteAddress,
      } for f in ns.functions]

      contents = template.render({
        "use_pch": False,
        "context": self.binary_context,
        "include_paths": sorted(includes),
        "using_paths": sorted(includes),
        "namespace_path": ns.namespace(ctx=self.esci),
        "functions": functions,
        "ifdef_expose_original": self.esci.macro_rules.ifdef_expose_original,
      })

      # TODO: make Namespace fix location info just like classes
      return ExportContents(path=dst, contents=contents)
    
  def export_namespaced_functions_funcfile(self, ns: Namespace, reimplementation_unifier: str | None = None):
    if self.template_path != DEFAULT_TEMPLATE_PATH:
      raise Exception()
    anchor, *names = self.template_path.split(".")
    with path(anchor, *names) as p:
      env = Environment(loader=FileSystemLoader(str(p)))
      template = env.get_template("NamespaceFunc.j2")

      includes = OrderedSet[str]()
      for f in ns.functions:
        includes += list(f.includes(self.esci))

      dst = f"{ns.location(ctx=self.esci)}.func.hpp"
      includes += self._inject_includes(includes, dst)

      functions = [{
        "returnType": f.return_type(ctx=self.esci)[0], 
        "name": sanitize_name(f.name.split("::")[-1]), # split if necessary (mistake in export)
        "parameters": [f"{type_name} {sanitize_name(name)}" for type_name, name in f.parameters(ctx=self.esci)] + (["..."] * f.has_varargs()),
        "callingConvention": sanitize_calling_convention(f.f.properties.additionalProperties.callingConvention),
        "address": f.f.locations[0].physicalLocation.address.absoluteAddress,
        "reimplemented": reimplementation_unifier if reimplementation_unifier else "false",
      } for f in ns.functions]

      contents = template.render({
        "use_pch": False,
        "context": self.binary_context,
        "include_paths": sorted(includes) + [
          f"{ns.location(ctx=self.esci)}.hpp"
        ],
        "using_paths": sorted(includes),
        "namespace_path": ns.namespace(ctx=self.esci),
        "functions": functions,
        "ifdef_expose_original": self.esci.macro_rules.ifdef_expose_original,
      })

      # TODO: make Namespace fix location info just like classes
      return ExportContents(path=dst, contents=contents)

  def export_namespaced_functions_body(self, ns: Namespace):
    if self.template_path != DEFAULT_TEMPLATE_PATH:
      raise Exception()
    anchor, *names = self.template_path.split(".")
    with path(anchor, *names) as p:
      env = Environment(loader=FileSystemLoader(str(p)))
      template = env.get_template("NamespaceCPP.j2")

      includes = OrderedSet[str]()
      for f in ns.functions:
        includes += list(f.includes(self.esci))
      
      dst = f"{ns.location(ctx=self.esci)}.cpp"
      includes += self._inject_includes(includes, dst)

      functions = [{
        "returnType": f.return_type(ctx=self.esci)[0], 
        "name": sanitize_name(f.name.split("::")[-1]), # split if necessary (mistake in export)
        "parameters": [f"{type_name} {sanitize_name(name)}" for type_name, name in f.parameters(ctx=self.esci)],
        "parameter_names": [f"{sanitize_name(name)}" for type_name, name in f.parameters(ctx=self.esci)],
        "callingConvention": sanitize_calling_convention(f.f.properties.additionalProperties.callingConvention),
        "address": f.f.locations[0].physicalLocation.address.absoluteAddress,
      } for f in ns.functions]

      contents = template.render({
        "use_pch": False,
        "context": self.binary_context,
        "include_paths": sorted(includes) + [
          f"{ns.location(ctx=self.esci)}.hpp"
        ],
        "using_paths": sorted(includes),
        "namespace_path": ns.namespace(ctx=self.esci),
        "functions": functions,
      })

      # TODO: make Namespace fix location info just like classes
      return ExportContents(path=f"{ns.location(ctx=self.esci)}.cpp", contents=contents, no_touch=False)

  def export_namespaced_function_body(self, ns: Namespace, f: Function):
    if self.template_path != DEFAULT_TEMPLATE_PATH:
      raise Exception()
    anchor, *names = self.template_path.split(".")
    with path(anchor, *names) as p:
      env = Environment(loader=FileSystemLoader(str(p)))
      template = env.get_template("NamespaceCPP.j2")

      includes = OrderedSet[str]()
      includes += list(f.includes(self.esci))

      dst = f"{ns.location(ctx=self.esci)}/{sanitize_name(f.name.split("::")[-1])}.cpp"
      includes += self._inject_includes(includes, dst)

      functions = [{
        "returnType": f.return_type(ctx=self.esci)[0], 
        "name": sanitize_name(f.name.split("::")[-1]), # split if necessary (mistake in export)
        "parameters": [f"{type_name} {sanitize_name(name)}" for type_name, name in f.parameters(ctx=self.esci)],
        "parameter_names": [f"{sanitize_name(name)}" for type_name, name in f.parameters(ctx=self.esci)],
        "callingConvention": sanitize_calling_convention(f.f.properties.additionalProperties.callingConvention),
        "address": f.f.locations[0].physicalLocation.address.absoluteAddress,
      }]

      contents = template.render({
        "use_pch": False,
        "context": self.binary_context,
        "include_paths": sorted(includes) + [
          f"{ns.location(ctx=self.esci)}/{ns.name}.hpp"
        ],
        "using_paths": sorted(includes),
        "namespace_path": ns.namespace(ctx=self.esci),
        "functions": functions,
      })

      # TODO: make Namespace fix location info just like classes
      return ExportContents(path=dst, contents=contents, no_touch=False)


  def export_namespace(self, ns: Namespace, export_bodies: bool = True, reimplementation_unifier: str | None = None) -> List[ExportContents]:
    dst = f"{ns.location(ctx=self.esci)}.hpp"
    if self.is_excluded_file(dst):
      return []
    if not export_bodies:
      return [
          self.export_namespaced_functions_header(ns),
          self.export_namespaced_functions_funcfile(ns, reimplementation_unifier),
      ]
    if self.esci.file_rules.one_file_per_function:
      return [
        self.export_namespaced_functions_header(ns),
        self.export_namespaced_functions_funcfile(ns, reimplementation_unifier),
        *[self.export_namespaced_function_body(ns, f) for f in ns.functions],
      ]  
    return [
      self.export_namespaced_functions_header(ns),
      self.export_namespaced_functions_funcfile(ns, reimplementation_unifier),
      self.export_namespaced_functions_body(ns),
    ]
  
  def export_helpers(self, dst_folder: str = "precomp"):
    if self.template_path != DEFAULT_TEMPLATE_PATH:
      raise Exception()
    anchor, *names = self.template_path.split(".")
    with path(anchor, *names) as p:
      env = Environment(loader=FileSystemLoader(str(p)))
      return [
        ExportContents(path=f"{dst_folder}/assertion.h", contents=env.get_template("Helpers_Assertion.j2").render()),
        ExportContents(path=f"{dst_folder}/common.hpp", contents=env.get_template("Helpers_Common.j2").render()),
      ]
  
  def export_symbol(self, address: int, name: str, defined_data: DefinedDataResult, destination: str, namespace: str):
    if self.template_path != DEFAULT_TEMPLATE_PATH:
      raise Exception()
    anchor, *names = self.template_path.split(".")
    with path(anchor, *names) as p:
      env = Environment(loader=FileSystemLoader(str(p)))
      template = env.get_template("DefinedDataH.j2")

      dst = f"{destination}/{sanitize_name(name)}.hpp"

      type_name, type_loc = remap_type(type_name = defined_data.properties.additionalProperties.typeName, type_loc = defined_data.properties.additionalProperties.typeLocation, ctx=self.esci)
      includes = OrderedSet(includes_for_type_name_location(type_name,
                                                      type_loc,
                                                      ctx=self.esci))
      includes += self._inject_includes(includes, dst)

      full_type_name = type_name
      if type_loc and type_loc != "/":
        if not type_loc.endswith(".hpp") and not type_loc.endswith(".h"):
          type_loc = transform_location(type_loc, self.esci)
          if type_loc and type_loc != "/":        
            if not type_loc.endswith(".hpp") and not type_loc.endswith(".h"):
              full_type_name = f"{type_loc.replace('/', "::")}::{type_name}"

      contents = template.render({
        "use_pch": False,
        "include_paths": sorted(includes),
        "using_paths": sorted(includes),
        "namespace_path": namespace,
        "name": name,
        "type_name": type_name,
        "full_type_name": full_type_name,
        "create_global_annotation_helper": len(includes) > 0,
        "address": address,
        "context": self.binary_context,
      })
    
      return ExportContents(path=dst, contents=contents)

  def export_symbols(self, i: Iterable[Tuple[int, str, DefinedDataResult]], destination: str, namespace:str):
    return [self.export_symbol(address, name, defined_data, destination, namespace) for address, name, defined_data in i]

  def export_symbols_as_assembly(self, 
                                 i: Iterable[Tuple[int, str, DefinedDataResult, BasicDataTypeResult | None, bool]], 
                                 destination: str, 
                                 typedefs: Dict[Tuple[str, str], Tuple[str, str, str]] = {}, 
                                 typedef_func: Callable[[str, str, str], Tuple[str, str, str]] = (lambda x, y, z: (x, y, z))):
    if self.template_path != DEFAULT_TEMPLATE_PATH:
      raise Exception()
    anchor, *names = self.template_path.split(".")
    with path(anchor, *names) as p:
      env = Environment(loader=FileSystemLoader(str(p)))
      template = env.get_template("Symbol_ASM.j2")

      type_symbols = []
      for address, name, ddr, dtr, isClass in i:
        #if address != 14630172: #TODO: debug line, remove!
        #  continue
        prefix = ""
        prop = ddr.properties.additionalProperties
        type_name, type_loc = remap_type(type_name = prop.typeName, type_loc = prop.typeLocation, ctx=self.esci)
        type_loc, type_name = loc_name_to_loc_name(transform_location(type_loc, ctx=self.esci), type_name)
        if (type_loc, type_name) in typedefs:
          type_loc, type_name, prefix = typedefs[(type_loc, type_name)]
        type_loc, type_name, prefix = typedef_func(type_loc, type_name, prefix)
        primitive = prefix == ""
        if dtr:
          if dtr.message.text == "DT.Union":
            prefix = "union "
          elif dtr.message.text == "DT.Struct":
            prefix = "struct " if not isClass else "class "            
        if type_loc in ["/"]:
          primitive = True

        m_base_type = re.match("^([A-Za-z_0-9]+)(.*)$", type_name)
        assert m_base_type
        base_type = m_base_type.group(1)
        if base_type in TYPEDEFS_COMMON:
          type_name = TYPEDEFS_COMMON[base_type] + m_base_type.group(2)
          primitive = True
          type_loc = "/"
          prefix = ""

        if type_name == "GUID":
          primitive = True
          type_name = "_GUID"
          type_loc = "/"
          prefix = "struct "          

        if prefix:
          primitive = False
        if primitive:
          t = _parse_type(f"{prefix}{type_name}")
        else:
          t = _parse_type(f"{prefix}{'::'.join(loc_name_to_parts(type_loc, type_name))}")
        
        type_symbols.append((build_extern_symbol(t, address), address))

      contents = template.render({
        "type_symbols": type_symbols,
      })
    return ExportContents(path=f"{destination}", contents=contents, include_preamble=False)

  # def export_symbols_as_assembly(self, i: Iterable[Tuple[int, str, DefinedDataResult, BasicDataTypeResult | None, bool]], destination: str, namespace:str):
  #   if self.template_path != DEFAULT_TEMPLATE_PATH:
  #     raise Exception()
  #   anchor, *names = self.template_path.split(".")
  #   with path(anchor, *names) as p:
  #     env = Environment(loader=FileSystemLoader(str(p)))
  #     template = env.get_template("Symbol_ASM.j2")

  #     type_symbols = []
  #     for address, name, defined_data, dtr, isClass in i:
  #       type_name, type_loc = remap_type(type_name = defined_data.properties.additionalProperties.typeName, type_loc = defined_data.properties.additionalProperties.typeLocation, ctx=self.esci)
  #       full_type_name = type_name
  #       primitive = dtr is None
  #       ns = []
  #       if type_loc and type_loc != "/":
  #         if not type_loc.endswith(".hpp") and not type_loc.endswith(".h"):
  #           primitive = False
  #           type_loc = transform_location(type_loc, self.esci)
  #           if type_loc and type_loc != "/":        
  #             if not type_loc.endswith(".hpp") and not type_loc.endswith(".h"):
  #               full_type_name = f"{type_loc.replace('/', "::")}::{type_name}"
  #               ns = type_loc.replace('/', "::").split("::")

  #       if primitive:
  #         if type_name in PRIMITIVES:
  #           type_symbols.append((encode_extern_instance(PrimitiveType.from_name(type_name), address), address))
  #         elif type_name == "GUID":
  #           type_symbols.append((encode_extern_instance(StructType(ns = [], name=f"_{type_name}"), address), address))
  #         elif type_name == "void*":
  #           type_symbols.append((encode_extern_instance(PointerType(typ=PrimitiveType.from_name("void")), address), address))
  #         elif type_name.count("[") == 1:
  #           m = re.match("([A-Za-z]+)\\[([0-9]+)\\]", type_name)
  #           base_type = m.group(1)
  #           dim1_size = int(m.group(2))
  #           type_symbols.append((encode_extern_instance(ArrayType(element=PrimitiveType.from_name(base_type), count=dim1_size), address), address))
  #         else:
  #           raise Exception(f"type not in primitives list: {full_type_name}; {name}")
          
  #       else:
  #         if isClass:
  #           type_symbols.append((encode_extern_instance(ClassType(ns = ns, name=type_name), address), address))
  #         else:
  #           typ = dtr.message.text if dtr else ""
  #           if typ == "DT.Struct":
  #             type_symbols.append((encode_extern_instance(StructType(ns = ns, name=type_name), address), address))
  #           elif typ == "DT.Union":
  #             raise Exception("Union not yet implemented")
  #           else:
  #             raise Exception(f"unknown type {typ}: {hex(address)} {defined_data} {dtr}")

  #     contents = template.render({
  #       "type_symbols": type_symbols,
  #     })
  #   return ExportContents(path=f"{destination}/symbols.asm", contents=contents)
      