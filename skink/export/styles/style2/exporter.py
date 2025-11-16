from jinja2 import Environment, FileSystemLoader
from importlib.resources import path

from skink.architecture.functionsignatures import FunctionSignature
from skink.architecture.namespaces.namespace import Namespace
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
from skink.export.context import DEFAULT, Context, TransformationRules
from skink.architecture.common.sanitization import sanitize_name

from typing import List, Iterable

from dataclasses import dataclass
from dataclasses_json import dataclass_json

DEFAULT_TEMPLATE_PATH = "skink.export.styles.style1.templates"
EXPORT_SETTINGS_CLASS_INCLUDE: Context = DEFAULT.copy() # type: ignore
EXPORT_SETTINGS_CLASS_INCLUDE.include.functions_this_parameter_type = False
EXPORT_SETTINGS_CLASS_INCLUDE.include.prefix_include = False
EXPORT_SETTINGS_CLASS_INCLUDE.include.file_extension = ".hpp"

EXPORT_SETTINGS_CLASS_INCLUDE.struct_rules.field_eol_char = False

EXPORT_SETTINGS_CLASS_INCLUDE.class_rules.export_constructor = False

EXPORT_SETTINGS_CLASS_SHIM_FILENAME: Context = DEFAULT.copy() # type: ignore
EXPORT_SETTINGS_CLASS_SHIM_FILENAME.class_rules.suffix = "_"


@dataclass
class BinaryContext:
  hash: str = "HASH"
  abbreviation: str = "ABBREV"
  reccmp_binary: str = "BIN"


DEFAULT_BINARY_CONTEXT: BinaryContext = BinaryContext()

class Exporter(object):
  
  def __init__(self, template_path: str = DEFAULT_TEMPLATE_PATH, binary_context: BinaryContext = DEFAULT_BINARY_CONTEXT,
               transformation_rules: TransformationRules = TransformationRules(),
               expose_original_methods: bool = False):
    self.template_path = template_path
    self.binary_context = binary_context
    # self.transformation_rules = transformation_rules
    self.esci: Context = EXPORT_SETTINGS_CLASS_INCLUDE.copy()
    self.esci.location_rules.transformation_rules = transformation_rules.copy()
    self.escsf: Context = EXPORT_SETTINGS_CLASS_SHIM_FILENAME.copy()
    self.escsf.location_rules.transformation_rules = transformation_rules.copy()
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

      includes = OrderedSet[str]()
      for m in c.functions(self.esci):
        includes += list(m.includes(self.esci))

      methods = [{
        "returnType": f.f.properties.additionalProperties.ret.typeName, 
        "name": sanitize_name(f.name.split("::")[-1]), # split if necessary (mistake in export)
        "parameters": [f"{param.typeName} {sanitize_name(param.name)}" for param in f.f.properties.additionalProperties.params if param.name != "this"],
      } for f in c.functions(self.esci)]

      contents = template.render({
        "use_pch": True,
        "include_paths": sorted(includes) + [f"{c.location(ctx=self.esci)}/{c.name}Struct.hpp"],
        "using_paths": sorted(includes),
        "namespace_path": c.namespace(ctx=self.esci),
        "class_name": f"{c.name}Class",
        "struct_name": f"{c.name}Struct",
        "class_size": c.structure.s.properties.additionalProperties.size,
        "methods": methods,
        "constructor": {
          "returnType": c.constructor.f.properties.additionalProperties.ret.typeName, 
          "name": sanitize_name(c.constructor.name.split("::")[-1]), # split if necessary (mistake in export)
          "parameters": [f"{param.typeName} {sanitize_name(param.name)}" for param in c.constructor.f.properties.additionalProperties.params if param.name != "this"],
        } if c.constructor else None,
        "expose_original_methods": self.expose_original_methods,
      })

      return ExportContents(path=f"{c.location(ctx=self.esci)}/{c.name}Class.hpp", contents=contents)
    
  def export_class_header_shim(self, c: Class):
    if self.template_path != DEFAULT_TEMPLATE_PATH:
      raise Exception()
    anchor, *names = self.template_path.split(".")
    with path(anchor, *names) as p:

      includes = OrderedSet[str]()
      for m in c.functions(self.esci):
        includes += list(m.includes(self.esci))

      methods = [{
        "returnType": f.f.properties.additionalProperties.ret.typeName, 
        "name": sanitize_name(f.name.split("::")[-1]), # split if necessary (mistake in export)
        "parameters": [f"{param.typeName} {sanitize_name(param.name)}" for param in f.f.properties.additionalProperties.params if param.name != "this"],
      } for f in c.functions(self.esci)]

      env = Environment(loader=FileSystemLoader(str(p)))
      template = env.get_template("ClassH_.j2")

      contents = template.render({
        "use_pch": True,
        "include_paths": sorted(includes),
        "using_paths": sorted(includes),
        "namespace_path": c.namespace(ctx=self.esci),
        "class_name": f"{c.name}Class",
        "class_size": c.structure.s.properties.additionalProperties.size,
        "methods": methods,
        "constructor": {
          "returnType": c.constructor.f.properties.additionalProperties.ret.typeName, 
          "name": sanitize_name(c.constructor.name.split("::")[-1]), # split if necessary (mistake in export)
          "parameters": [f"{param.typeName} {sanitize_name(param.name)}" for param in c.constructor.f.properties.additionalProperties.params if param.name != "this"],
        } if c.constructor else None,
      })

      return ExportContents(path=f"{c.location(ctx=self.esci)}/{c.name}Class_.hpp", contents=contents)

  def export_class_struct_header(self, c: Class):
    if self.template_path != DEFAULT_TEMPLATE_PATH:
      raise Exception()
    anchor, *names = self.template_path.split(".")
    with path(anchor, *names) as p:
      s: Struct = c.structure
      env = Environment(loader=FileSystemLoader(str(p)))
      template = env.get_template("ClassStructH.j2")

      includes = OrderedSet(s.includes(self.esci))

      fields =  list({"string": s, "offset": o, "length": l} for s, o, l in s.export_field_declarations_with_offsets_and_lengths(self.esci))
      
      contents = template.render({
        "use_pch": True,
        "include_paths": sorted(includes),
        "using_paths": sorted(includes),
        "namespace_path": c.namespace(ctx=self.esci),
        "struct_name": s.name + "Struct",
        "struct_size": s.s.properties.additionalProperties.size,
        "fields": fields,
      })
    
      return ExportContents(path=f"{c.location(ctx=self.esci)}/{c.name}Struct.hpp", contents=contents)
  
  def export_class_body(self, c: Class):
    if self.template_path != DEFAULT_TEMPLATE_PATH:
      raise Exception()
    anchor, *names = self.template_path.split(".")
    with path(anchor, *names) as p:
      env = Environment(loader=FileSystemLoader(str(p)))
      template = env.get_template("ClassCPP.j2")

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
        "include_paths": sorted(includes) + [f"{c.location(ctx=self.esci)}/{c.name}Class.hpp"],
        "using_paths": sorted(includes),
        "namespace_path": c.namespace(ctx=self.esci),
        "class_name": f"{c.name}Class",
        "class_size": c.structure.s.properties.additionalProperties.size,
        "methods": methods,
      })

      return ExportContents(path=f"{c.location(ctx=self.esci)}/{c.name}Class.cpp", contents=contents, no_touch=False)

  def export_class_body_shim(self, c: Class):
    if self.template_path != DEFAULT_TEMPLATE_PATH:
      raise Exception()
    anchor, *names = self.template_path.split(".")
    with path(anchor, *names) as p:
      env = Environment(loader=FileSystemLoader(str(p)))
      template = env.get_template("ClassCPP_.j2")

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
        "include_paths": sorted(includes) + [
           f"{c.location(ctx=self.esci)}/{c.name}Namespace.hpp",
           f"{c.location(ctx=self.esci)}/{c.name}Class_.hpp",
        ],
        "using_paths": sorted(includes),
        "namespace_path": c.namespace(ctx=self.esci),
        "class_name": f"{c.name}Class",
        "class_size": c.structure.s.properties.additionalProperties.size,
        "methods": methods,
        "singleton_address": c.singleton.defined_data.address() if c.singleton else 0,
      })

      return ExportContents(path=f"{c.location(ctx=self.esci)}/{c.name}Class_.cpp", contents=contents)
    
  def export_class_namespace(self, c: Class):
    if self.template_path != DEFAULT_TEMPLATE_PATH:
      raise Exception()
    anchor, *names = self.template_path.split(".")
    with path(anchor, *names) as p:
      env = Environment(loader=FileSystemLoader(str(p)))
      template = env.get_template("ClassNamespaceH.j2")

      includes = OrderedSet[str]()
      for m in c.functions(self.esci):
        includes += list(m.includes(self.esci))

      methods = [{
        "returnType": f.f.properties.additionalProperties.ret.typeName, 
        "name": sanitize_name(f.name.split("::")[-1]), # split if necessary (mistake in export)
        "parameters": [f"{param.typeName} {sanitize_name(param.name)}" for param in f.f.properties.additionalProperties.params if param.name != "this"],
        "address": f.f.locations[0].physicalLocation.address.absoluteAddress,
      } for f in c.functions(self.esci)]

      contents = template.render({
        "use_pch": True,
        "context": self.binary_context,
        "include_paths": sorted(includes) + [
          f"{c.location(ctx=self.esci)}/{c.name}Class.hpp",
        ],
        "using_paths": sorted(includes),
        "namespace_path": c.namespace(ctx=self.esci),
        "class_name": f"{c.name}Class",
        "class_size": c.structure.s.properties.additionalProperties.size,
        "methods": methods,
        "singleton_name": f"DAT_{c.name}", # TODO: probably almost always correct?
        "expose_original_methods": self.expose_original_methods,
      })

      return ExportContents(path=f"{c.location(ctx=self.esci)}/{c.name}Namespace.hpp", contents=contents)

  def export_class_namespace_helper(self, c: Class):
    if self.template_path != DEFAULT_TEMPLATE_PATH:
      raise Exception()
    anchor, *names = self.template_path.split(".")
    with path(anchor, *names) as p:
      env = Environment(loader=FileSystemLoader(str(p)))
      template = env.get_template("IncludesOnlyH.j2")

      includes = [f"{c.location(ctx=self.esci)}/{c.name}Namespace.hpp"]
      contents = template.render({
        "use_pch": True,
        "include_paths": includes,
      })

      return ExportContents(path=f"{c.location(ctx=self.esci)}.hpp", contents=contents)
    
  def export_class(self, c: Class) -> List[ExportContents]:
    return [
      self.export_class_header(c),
      self.export_class_header_shim(c),
      self.export_class_struct_header(c),
      self.export_class_body(c),
      self.export_class_body_shim(c),
      self.export_class_namespace(c),
      self.export_class_namespace_helper(c),
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
      template2 = env.get_template("SizedEnum_CPP03_CPP.j2")

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

      path2 = f"{e.location(ctx=self.esci)}/{e.name}.cpp"
      contents2 = template2.render({
        "include_paths": [path1],
        "namespace_path": namespace_path,
        "name": sanitize_name(name),
        "type": type,
        "fields": fields,
      })

      return [ExportContents(path=path1, contents=contents1), ExportContents(path=path2, contents=contents2)]
    
  def export_function_signature(self, fs: FunctionSignature):
    if self.template_path != DEFAULT_TEMPLATE_PATH:
      raise Exception()
    anchor, *names = self.template_path.split(".")
    with path(anchor, *names) as p:
      env = Environment(loader=FileSystemLoader(str(p)))
      template1 = env.get_template("FunctionSignatureH.j2")

      namespace_path = fs.namespace(ctx=self.esci)
      include_paths: List[str] = []
      
      returnTypeName = fs.fsr.properties.additionalProperties.retType.name
      returnTypeLocation = fs.fsr.properties.additionalProperties.retType.location
      callingConvention = fs.fsr.properties.additionalProperties.callingConventionName

      parameters = [f"{sanitize_name(param.name)} " for param in fs.fsr.properties.additionalProperties.params if param.name != "this"]
      name = fs.fsr.properties.additionalProperties.name
      contents = template1.render({
        "include_paths": include_paths,
        "use_pch": True,
        "namespace_path": namespace_path,
        "name": sanitize_name(name),
        "parameters": parameters,
        "returnTypeName": returnTypeName,
        "returnTypeLocation": returnTypeLocation,
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
      include_paths: List[str] = []
      
      typeName = td.tr.properties.additionalProperties.type.name
      # typeLocation = td.tr.properties.additionalProperties.type.location

      name = td.tr.properties.additionalProperties.name
      contents = template1.render({
        "include_paths": include_paths,
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
        "callingConvention": f.f.properties.additionalProperties.callingConvention,
        "name": sanitize_name(f.name.split("::")[-1]), # split if necessary (mistake in export)
        "parameters": [f"{param.typeName} {sanitize_name(param.name)}" for param in f.f.properties.additionalProperties.params if param.name != "this"],
        "address": f.f.locations[0].physicalLocation.address.absoluteAddress,
      } for f in ns.functions]

      contents = template.render({
        "use_pch": True,
        "context": self.binary_context,
        "include_paths": sorted(includes),
        "using_paths": sorted(includes),
        "namespace_path": ns.namespace(ctx=self.esci),
        "functions": functions,
      })

      # TODO: make Namespace fix location info just like classes
      return ExportContents(path=f"{ns.location(ctx=self.esci)}/{ns.name}.hpp", contents=contents)

  def export_namespaced_functions_stubs(self, ns: Namespace):
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
        "callingConvention": f.f.properties.additionalProperties.callingConvention,
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
      return ExportContents(path=f"{ns.location(ctx=self.esci)}/{ns.name}.cpp", contents=contents)

  def export_namespace(self, ns: Namespace):
    return [
      self.export_namespaced_functions_header(ns),
      self.export_namespaced_functions_stubs(ns)
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
      ]