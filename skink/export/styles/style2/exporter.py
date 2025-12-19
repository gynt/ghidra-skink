from jinja2 import Environment, FileSystemLoader
from importlib.resources import path

from skink.architecture.functionsignatures import FunctionSignature
from skink.architecture.namespaces.namespace import Namespace
from skink.architecture.functions.function import Function
from skink.sarif.BasicResult import BasicResult
from skink.sarif.datatypes.EnumResult import EnumResult
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

from typing import List, Iterable

from dataclasses import dataclass
from dataclasses_json import dataclass_json

DEFAULT_TEMPLATE_PATH = "skink.export.styles.style2.templates"
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
               expose_original_methods: bool = False):
    self.template_path = template_path
    self.binary_context = binary_context
    # self.transformation_rules = transformation_rules
    self.esci: Context = EXPORT_SETTINGS_CLASS_INCLUDE.copy() # type: ignore
    self.esci.location_rules.transformation_rules = transformation_rules.copy() # type: ignore
    # self.escsf: Context = EXPORT_SETTINGS_CLASS_SHIM_FILENAME.copy() # type: ignore
    # self.escsf.location_rules.transformation_rules = transformation_rules.copy() # type: ignore
    self.expose_original_methods = expose_original_methods

  def export_addresses(self, objects: Iterable[BasicResult]):
    if self.template_path != DEFAULT_TEMPLATE_PATH:
      raise Exception()
    anchor, *names = self.template_path.split(".")
    with path(anchor, *names) as p:
      env = Environment(loader=FileSystemLoader(str(p)))
      template = env.get_template("AddressesH.j2")

      addresses: OrderedSet[int] = OrderedSet()

      for obj in objects:
        if isinstance(obj, DefinedDataResult):
          for l in obj.locations:
            addresses.add(l.physicalLocation.address.absoluteAddress)
        elif isinstance(obj, SymbolResult):
          for l in obj.locations:
            addresses.add(l.physicalLocation.address.absoluteAddress)
        elif isinstance(obj, FunctionResult):
          for l in obj.locations:
            addresses.add(l.physicalLocation.address.absoluteAddress)
      
      return ExportContents(path=f"Addresses/addresses-{self.binary_context.abbreviation}-{self.binary_context.hash}.hpp",
                            contents=template.render({
                              "context": self.binary_context,
                              "addresses": addresses,
                              "use_pch": True,
                            }),
                            no_touch=True)


  def export_class_header(self, c: Class):
    if self.template_path != DEFAULT_TEMPLATE_PATH:
      raise Exception()
    anchor, *names = self.template_path.split(".")
    with path(anchor, *names) as p:
      env = Environment(loader=FileSystemLoader(str(p)))
      template = env.get_template("ClassH.j2")

      if not c.structure:
        raise Exception()

      includes = OrderedSet[str](c.structure.includes(self.esci))
      for m in c.functions(self.esci):
        includes += list(m.includes(self.esci))

      methods = [{
        "returnType": f.f.properties.additionalProperties.ret.typeName, 
        "name": sanitize_name(f.name.split("::")[-1]), # split if necessary (mistake in export)
        "parameters": [f"{param.typeName} {sanitize_name(param.name)}" for param in f.f.properties.additionalProperties.params if param.name != "this"],
        "parameter_names": [f"{sanitize_name(param.name)}" for param in f.f.properties.additionalProperties.params if param.name != "this"],
        "address": f.f.locations[0].physicalLocation.address.absoluteAddress,
      } for f in c.functions(self.esci)]

      fields =  list({"string": s, "offset": o, "length": l} for s, o, l in c.structure.export_field_declarations_with_offsets_and_lengths(self.esci))

      contents = template.render({
        "use_pch": True,
        "include_paths": sorted(includes),
        "using_paths": sorted(includes),
        "namespace_path": c.namespace(ctx=self.esci),
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

      return ExportContents(path=f"{c.location(ctx=self.esci)}/{c.name}.hpp", contents=contents)
  
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

      methods = [{
        "returnType": f.f.properties.additionalProperties.ret.typeName, 
        "name": sanitize_name(f.name.split("::")[-1]), # split if necessary (mistake in export)
        "parameters": [f"{param.typeName} {sanitize_name(param.name)}" for param in f.f.properties.additionalProperties.params if param.name != "this"],
        "parameter_names": [f"{sanitize_name(param.name)}" for param in f.f.properties.additionalProperties.params if param.name != "this"],
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

      return ExportContents(path=f"{c.location(ctx=self.esci)}/{c.name}.cpp", contents=contents, no_touch=False)
  
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

      methods = [{
        "returnType": f.f.properties.additionalProperties.ret.typeName, 
        "name": sanitize_name(f.name.split("::")[-1]), # split if necessary (mistake in export)
        "parameters": [f"{param.typeName} {sanitize_name(param.name)}" for param in f.f.properties.additionalProperties.params if param.name != "this"],
        "parameter_names": [f"{sanitize_name(param.name)}" for param in f.f.properties.additionalProperties.params if param.name != "this"],
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

      return ExportContents(path=f"{c.location(ctx=self.esci)}/{c.name}/{sanitize_name(f.name)}.cpp", contents=contents, no_touch=False)
  

  def export_class(self, c: Class) -> List[ExportContents]:
    if self.esci.file_rules.one_file_per_method:
      return [
        self.export_class_header(c),
        *[self.export_class_body_method(c, f) for f in c.functions(self.esci)],
      ]  
    return [
      self.export_class_header(c),
      self.export_class_body(c),
    ]
    
  def export_struct(self, s: Struct):
    if self.template_path != DEFAULT_TEMPLATE_PATH:
      raise Exception()
    anchor, *names = self.template_path.split(".")
    with path(anchor, *names) as p:
      env = Environment(loader=FileSystemLoader(str(p)))
      template = env.get_template("StructH.j2")

      includes = OrderedSet(s.includes(self.esci))

      fields =  list({"string": s, "offset": o, "length": l} for s, o, l in s.export_field_declarations_with_offsets_and_lengths(self.esci))
      
      contents = template.render({
        "use_pch": True,
        "include_paths": sorted(includes),
        "using_paths": sorted(includes),
        "namespace_path": s.namespace(ctx=self.esci),
        "struct_name": sanitize_name(s.name),
        "struct_size": s.s.properties.additionalProperties.size,
        "fields": fields,
      })
    
      return ExportContents(path=f"{s.location(ctx=self.esci)}/{s.name}.hpp", contents=contents)

  def export_struct_singleton(self, s: Struct):
    if self.template_path != DEFAULT_TEMPLATE_PATH:
      raise Exception()
    anchor, *names = self.template_path.split(".")
    with path(anchor, *names) as p:
      env = Environment(loader=FileSystemLoader(str(p)))
      template = env.get_template("StructH.j2")

      includes = OrderedSet(s.includes(self.esci))

      fields =  list({"string": s, "offset": o, "length": l} for s, o, l in s.export_field_declarations_with_offsets_and_lengths(self.esci))
      
      contents = template.render({
        "use_pch": True,
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
    
      return ExportContents(path=f"{s.location(ctx=self.esci)}/{s.name}.hpp", contents=contents)


  def export_union(self, u: Union):
    if self.template_path != DEFAULT_TEMPLATE_PATH:
      raise Exception()
    anchor, *names = self.template_path.split(".")
    with path(anchor, *names) as p:
      env = Environment(loader=FileSystemLoader(str(p)))
      template = env.get_template("UnionH.j2")

      includes = OrderedSet(u.includes(self.esci))

      fields =  list({"string": s, "offset": o, "length": l} for s, o, l in u.export_field_declarations_with_offsets_and_lengths(self.esci))
      
      contents = template.render({
        "use_pch": True,
        "include_paths": sorted(includes),
        "using_paths": sorted(includes),
        "namespace_path": u.namespace(ctx=self.esci),
        "union_name": sanitize_name(u.name),
        "union_size": u.s.properties.additionalProperties.size,
        "fields": fields,
      })
    
      return ExportContents(path=f"{u.location(ctx=self.esci)}/{u.name}.hpp", contents=contents)

  def export_enum(self, e: Enum):
    if self.template_path != DEFAULT_TEMPLATE_PATH:
      raise Exception()
    anchor, *names = self.template_path.split(".")
    with path(anchor, *names) as p:
      env = Environment(loader=FileSystemLoader(str(p)))
      template1 = env.get_template("EnumH.j2")

      namespace_path = e.namespace(ctx=self.esci)

      fields = [{"name": sanitize_name(key), "value": value} for key, value in e.er.properties.additionalProperties.constants.items()]
      name = e.er.properties.additionalProperties.name
      type = e.er.properties.additionalProperties.base
      contents = template1.render({
        "use_pch": True,
        "namespace_path": namespace_path,
        "name": sanitize_name(name),
        "type": type,
        "fields": fields,
      })
      return ExportContents(path=f"{e.location(ctx=self.esci)}/{e.name}.hpp", contents=contents)


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
        "use_pch": True,
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
    anchor, *names = self.template_path.split(".")
    with path(anchor, *names) as p:
      env = Environment(loader=FileSystemLoader(str(p)))
      template1 = env.get_template("FunctionSignatureH.j2")

      namespace_path = fs.namespace(ctx=self.esci)
      include_paths: OrderedSet[str] = OrderedSet[str]()
      include_paths += fs.includes(ctx=self.esci)
      
      returnTypeName = fs.fsr.properties.additionalProperties.retType.name
      returnTypeLocation = fs.fsr.properties.additionalProperties.retType.location
      callingConvention = sanitize_calling_convention(fs.fsr.properties.additionalProperties.callingConventionName)

      # Function signature parameter names are the types...
      parameters = [f"{param.name} " for param in fs.fsr.properties.additionalProperties.params if param.name != "this"]
      name = fs.fsr.properties.additionalProperties.name
      contents = template1.render({
        "include_paths": sorted(include_paths),
        "using_paths": sorted(include_paths),
        "use_pch": True,
        "namespace_path": namespace_path,
        "name": sanitize_name(name),
        "parameters": parameters,
        "returnTypeName": returnTypeName,
        "returnTypeLocation": returnTypeLocation,
        "callingConvention": callingConvention,
        # "type": type,
      })
      return ExportContents(path=f"{fs.location(ctx=self.esci)}/{fs.name}.hpp", contents=contents)

  def export_typedef(self, td: Typedef):
    if self.template_path != DEFAULT_TEMPLATE_PATH:
      raise Exception()
    anchor, *names = self.template_path.split(".")
    with path(anchor, *names) as p:
      env = Environment(loader=FileSystemLoader(str(p)))
      template1 = env.get_template("TypedefH.j2")

      namespace_path = td.namespace(ctx=self.esci)
      include_paths: OrderedSet[str] = OrderedSet[str]()
      include_paths += td.includes(ctx=self.esci)
      
      typeName = td.tr.properties.additionalProperties.type.name
      if not typeName:
        typeName = td.tr.properties.additionalProperties.typeName
      # typeLocation = td.tr.properties.additionalProperties.type.location

      name = td.tr.properties.additionalProperties.name
      contents = template1.render({
        "include_paths": sorted(include_paths),
        "using_paths": sorted(include_paths),
        "use_pch": True,
        "namespace_path": namespace_path,
        "name": sanitize_name(name),
        "type": typeName,
        # "returnTypeLocation": typeLocation,
        # "type": type,
      })
      return ExportContents(path=f"{td.location(ctx=self.esci)}/{td.name}.hpp", contents=contents)
  
  def export_namespaced_functions_header(self, ns: Namespace):
    if self.template_path != DEFAULT_TEMPLATE_PATH:
      raise Exception()
    anchor, *names = self.template_path.split(".")
    with path(anchor, *names) as p:
      env = Environment(loader=FileSystemLoader(str(p)))
      template = env.get_template("NamespaceH.j2")

      includes = OrderedSet[str]()
      for f in ns.functions:
        includes += list(f.includes(self.esci))

      functions = [{
        "returnType": f.f.properties.additionalProperties.ret.typeName, 
        "callingConvention": sanitize_calling_convention(f.f.properties.additionalProperties.callingConvention),
        "name": sanitize_name(f.name.split("::")[-1]), # split if necessary (mistake in export)
        "parameters": [f"{param.typeName} {sanitize_name(param.name)}" for param in f.f.properties.additionalProperties.params if param.name != "this"],
        "parameter_names": [f"{sanitize_name(param.name)}" for param in f.f.properties.additionalProperties.params if param.name != "this"],
        "address": f.f.locations[0].physicalLocation.address.absoluteAddress,
      } for f in ns.functions]

      contents = template.render({
        "use_pch": True,
        "context": self.binary_context,
        "include_paths": sorted(includes),
        "using_paths": sorted(includes),
        "namespace_path": ns.namespace(ctx=self.esci),
        "functions": functions,
        "ifdef_expose_original": self.esci.macro_rules.ifdef_expose_original,
      })

      # TODO: make Namespace fix location info just like classes
      return ExportContents(path=f"{ns.location(ctx=self.esci)}/{ns.name}.hpp", contents=contents)

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

      functions = [{
        "returnType": f.f.properties.additionalProperties.ret.typeName, 
        "callingConvention": sanitize_calling_convention(f.f.properties.additionalProperties.callingConvention),
        "name": sanitize_name(f.name.split("::")[-1]), # split if necessary (mistake in export)
        "parameters": [f"{param.typeName} {sanitize_name(param.name)}" for param in f.f.properties.additionalProperties.params if param.name != "this"],
        "parameter_names": [f"{sanitize_name(param.name)}" for param in f.f.properties.additionalProperties.params if param.name != "this"],
        "address": f.f.locations[0].physicalLocation.address.absoluteAddress,
      } for f in ns.functions]

      contents = template.render({
        "use_pch": True,
        "context": self.binary_context,
        "include_paths": sorted(includes) + [
          f"{ns.location(ctx=self.esci)}/{ns.name}.hpp"
        ],
        "using_paths": sorted(includes),
        "namespace_path": ns.namespace(ctx=self.esci),
        "functions": functions,
      })

      # TODO: make Namespace fix location info just like classes
      return ExportContents(path=f"{ns.location(ctx=self.esci)}/{ns.name}.cpp", contents=contents, no_touch=False)

  def export_namespaced_function_body(self, ns: Namespace, f: Function):
    if self.template_path != DEFAULT_TEMPLATE_PATH:
      raise Exception()
    anchor, *names = self.template_path.split(".")
    with path(anchor, *names) as p:
      env = Environment(loader=FileSystemLoader(str(p)))
      template = env.get_template("NamespaceCPP.j2")

      includes = OrderedSet[str]()
      includes += list(f.includes(self.esci))

      functions = [{
        "returnType": f.f.properties.additionalProperties.ret.typeName, 
        "callingConvention": sanitize_calling_convention(f.f.properties.additionalProperties.callingConvention),
        "name": sanitize_name(f.name.split("::")[-1]), # split if necessary (mistake in export)
        "parameters": [f"{param.typeName} {sanitize_name(param.name)}" for param in f.f.properties.additionalProperties.params if param.name != "this"],
        "parameter_names": [f"{sanitize_name(param.name)}" for param in f.f.properties.additionalProperties.params if param.name != "this"],
        "address": f.f.locations[0].physicalLocation.address.absoluteAddress,
      }]

      contents = template.render({
        "use_pch": True,
        "context": self.binary_context,
        "include_paths": sorted(includes) + [
          f"{ns.location(ctx=self.esci)}/{ns.name}.hpp"
        ],
        "using_paths": sorted(includes),
        "namespace_path": ns.namespace(ctx=self.esci),
        "functions": functions,
      })

      # TODO: make Namespace fix location info just like classes
      return ExportContents(path=f"{ns.location(ctx=self.esci)}/{ns.name}/{sanitize_name(f.name)}.cpp", contents=contents, no_touch=False)


  def export_namespace(self, ns: Namespace) -> List[ExportContents]:
    if self.esci.file_rules.one_file_per_function:
      return [
        self.export_namespaced_functions_header(ns),
        *[self.export_namespaced_function_body(ns, f) for f in ns.functions],
      ]  
    return [
      self.export_namespaced_functions_header(ns),
      self.export_namespaced_functions_body(ns),
    ]
  
  def export_helpers(self, dst_folder: str = "util"):
    if self.template_path != DEFAULT_TEMPLATE_PATH:
      raise Exception()
    anchor, *names = self.template_path.split(".")
    with path(anchor, *names) as p:
      env = Environment(loader=FileSystemLoader(str(p)))
      return [
        ExportContents(path=f"{dst_folder}/assertion.h", contents=env.get_template("Helpers_Assertion.j2").render()),
        ExportContents(path=f"{dst_folder}/interfacing/DataReference.h", contents=env.get_template("Helpers_DataReference.j2").render()),
        ExportContents(path=f"{dst_folder}/interfacing/MemberFunctionPointerGenerator.h", contents=env.get_template("Helpers_MemberFunctionPointerGenerator.j2").render()),
        ExportContents(path=f"{dst_folder}/interfacing/common.hpp", contents=env.get_template("Helpers_Common.j2").render()),
      ]