from jinja2 import Environment, FileSystemLoader
from importlib.resources import path

from skink.sarif.BasicResult import BasicResult
from skink.sarif.datatypes.EnumResult import EnumResult
from skink.sarif.defineddata.DefinedDataResult import DefinedDataResult
from skink.sarif.symbols.symbol import SymbolResult
from skink.sarif.functions.FunctionResult import FunctionResult
from skink.architecture.classes.cls import Class
from skink.architecture.structs.struct import Struct
from skink.architecture.enums import Enum
from skink.export.project.exportcontents import ExportContents
from skink.utils.OrderedSet import OrderedSet
from skink.export.context import DEFAULT, Context

from typing import List, Iterable

from dataclasses import dataclass
from dataclasses_json import dataclass_json

DEFAULT_TEMPLATE_PATH = "skink.export.templates"
EXPORT_SETTINGS_CLASS_INCLUDE: Context = DEFAULT.copy()
EXPORT_SETTINGS_CLASS_INCLUDE.include = EXPORT_SETTINGS_CLASS_INCLUDE.include.mutate(functions_this_parameter_type=False, prefix_include=False)
EXPORT_SETTINGS_CLASS_INCLUDE.struct_rules = EXPORT_SETTINGS_CLASS_INCLUDE.struct_rules.mutate(field_eol_char = False)
EXPORT_SETTINGS_CLASS_INCLUDE.location_rules = EXPORT_SETTINGS_CLASS_INCLUDE.location_rules.mutate(transformation_rules = EXPORT_SETTINGS_CLASS_INCLUDE.location_rules.transformation_rules.mutate(use_regex = True, regex={"_HoldStrong": "EXE"}))
EXPORT_SETTINGS_CLASS_INCLUDE.class_rules = EXPORT_SETTINGS_CLASS_INCLUDE.class_rules.mutate(export_constructor = False)

EXPORT_SETTINGS_CLASS_SHIM_FILENAME = DEFAULT.copy()
EXPORT_SETTINGS_CLASS_SHIM_FILENAME.class_rules = EXPORT_SETTINGS_CLASS_SHIM_FILENAME.class_rules.mutate(suffix = "_")
EXPORT_SETTINGS_CLASS_SHIM_FILENAME.location_rules = EXPORT_SETTINGS_CLASS_SHIM_FILENAME.location_rules.mutate(transformation_rules = EXPORT_SETTINGS_CLASS_SHIM_FILENAME.location_rules.transformation_rules.mutate(use_regex = True, regex={"_HoldStrong": "EXE"}))


@dataclass
@dataclass_json
class BinaryContext:
  hash: str = "3bb0a8c1"
  abbreviation: str = "shc"
  reccmp_binary: str = "STRONGHOLDCRUSADER"



DEFAULT_BINARY_CONTEXT: BinaryContext = BinaryContext()

class Exporter(object):
  
  def __init__(self, template_path: str = DEFAULT_TEMPLATE_PATH, binary_context: BinaryContext = DEFAULT_BINARY_CONTEXT):
    self.template_path = template_path
    self.binary_context = binary_context

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
      
      return ExportContents(path=f"Addresses/addresses-{self.binary_context.abbreviation}-{self.binary_context.hash}.h",
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
      for m in c.functions(EXPORT_SETTINGS_CLASS_INCLUDE):
        includes += list(m.includes(EXPORT_SETTINGS_CLASS_INCLUDE))

      methods = [{
        "returnType": f.f.properties.additionalProperties.ret.typeName, 
        "name": f.name.split("::")[-1], # split if necessary (mistake in export)
        "parameters": [f"{param.typeName} {param.name}" for param in f.f.properties.additionalProperties.params if param.name != "this"],
      } for f in c.functions(EXPORT_SETTINGS_CLASS_INCLUDE)]

      contents = template.render({
        "use_pch": True,
        "include_paths": sorted(includes) + [f"{c.location(ctx=EXPORT_SETTINGS_CLASS_INCLUDE)}/{c.name}Struct.h"],
        "using_paths": sorted(includes),
        "namespace_path": c.namespace(ctx=EXPORT_SETTINGS_CLASS_INCLUDE),
        "class_name": f"{c.name}Class",
        "struct_name": f"{c.name}Struct",
        "class_size": c.structure.s.properties.additionalProperties.size,
        "methods": methods,
        "constructor": {
          "returnType": c.constructor.f.properties.additionalProperties.ret.typeName, 
          "name": c.constructor.name.split("::")[-1], # split if necessary (mistake in export)
          "parameters": [f"{param.typeName} {param.name}" for param in c.constructor.f.properties.additionalProperties.params if param.name != "this"],
        } if c.constructor else None,
      })

      return ExportContents(path=f"{c.location(ctx=EXPORT_SETTINGS_CLASS_INCLUDE)}/{c.name}Class.h", contents=contents)
    
  def export_class_header_shim(self, c: Class):
    if self.template_path != DEFAULT_TEMPLATE_PATH:
      raise Exception()
    anchor, *names = self.template_path.split(".")
    with path(anchor, *names) as p:

      includes = OrderedSet[str]()
      for m in c.functions(EXPORT_SETTINGS_CLASS_INCLUDE):
        includes += list(m.includes(EXPORT_SETTINGS_CLASS_INCLUDE))

      methods = [{
        "returnType": f.f.properties.additionalProperties.ret.typeName, 
        "name": f.name.split("::")[-1], # split if necessary (mistake in export)
        "parameters": [f"{param.typeName} {param.name}" for param in f.f.properties.additionalProperties.params if param.name != "this"],
      } for f in c.functions(EXPORT_SETTINGS_CLASS_INCLUDE)]

      env = Environment(loader=FileSystemLoader(str(p)))
      template = env.get_template("ClassH_.j2")

      contents = template.render({
        "use_pch": True,
        "include_paths": sorted(includes),
        "using_paths": sorted(includes),
        "namespace_path": c.namespace(ctx=EXPORT_SETTINGS_CLASS_INCLUDE),
        "class_name": f"{c.name}Class",
        "class_size": c.structure.s.properties.additionalProperties.size,
        "methods": methods,
        "constructor": {
          "returnType": c.constructor.f.properties.additionalProperties.ret.typeName, 
          "name": c.constructor.name.split("::")[-1], # split if necessary (mistake in export)
          "parameters": [f"{param.typeName} {param.name}" for param in c.constructor.f.properties.additionalProperties.params if param.name != "this"],
        } if c.constructor else None,
      })

      return ExportContents(path=f"{c.location(ctx=EXPORT_SETTINGS_CLASS_INCLUDE)}/{c.name}Class_.h", contents=contents)

  def export_class_struct_header(self, c: Class):
    if self.template_path != DEFAULT_TEMPLATE_PATH:
      raise Exception()
    anchor, *names = self.template_path.split(".")
    with path(anchor, *names) as p:
      s: Struct = c.structure
      env = Environment(loader=FileSystemLoader(str(p)))
      template = env.get_template("ClassStructH.j2")

      includes = OrderedSet(s.includes(EXPORT_SETTINGS_CLASS_INCLUDE))

      fields =  list({"string": s, "offset": o, "length": l} for s, o, l in s.export_field_declarations_with_offsets_and_lengths(EXPORT_SETTINGS_CLASS_INCLUDE))
      
      contents = template.render({
        "use_pch": True,
        "include_paths": sorted(includes),
        "using_paths": sorted(includes),
        "namespace_path": c.namespace(ctx=EXPORT_SETTINGS_CLASS_INCLUDE),
        "struct_name": s.name + "Struct",
        "struct_size": s.s.properties.additionalProperties.size,
        "fields": fields,
      })
    
      return ExportContents(path=f"{c.location(ctx=EXPORT_SETTINGS_CLASS_INCLUDE)}/{c.name}Struct.h", contents=contents)
  
  def export_class_body(self, c: Class):
    if self.template_path != DEFAULT_TEMPLATE_PATH:
      raise Exception()
    anchor, *names = self.template_path.split(".")
    with path(anchor, *names) as p:
      env = Environment(loader=FileSystemLoader(str(p)))
      template = env.get_template("ClassCPP.j2")

      includes = OrderedSet[str]()
      for m in c.functions(EXPORT_SETTINGS_CLASS_INCLUDE):
        includes += list(m.includes(EXPORT_SETTINGS_CLASS_INCLUDE))

      methods = [{
        "returnType": f.f.properties.additionalProperties.ret.typeName, 
        "name": f.name.split("::")[-1], # split if necessary (mistake in export)
        "parameters": [f"{param.typeName} {param.name}" for param in f.f.properties.additionalProperties.params if param.name != "this"],
        "parameter_names": [f"{param.name}" for param in f.f.properties.additionalProperties.params if param.name != "this"],
        "address": f.f.locations[0].physicalLocation.address.absoluteAddress,
      } for f in c.functions(EXPORT_SETTINGS_CLASS_INCLUDE)]

      contents = template.render({
        "context": self.binary_context,
        "include_paths": sorted(includes) + [f"{c.location(ctx=EXPORT_SETTINGS_CLASS_INCLUDE)}/{c.name}Class.h"],
        "using_paths": sorted(includes),
        "namespace_path": c.namespace(ctx=EXPORT_SETTINGS_CLASS_INCLUDE),
        "class_name": f"{c.name}Class",
        "class_size": c.structure.s.properties.additionalProperties.size,
        "methods": methods,
      })

      return ExportContents(path=f"{c.location(ctx=EXPORT_SETTINGS_CLASS_INCLUDE)}/{c.name}Class.cpp", contents=contents, no_touch=False)

  def export_class_body_shim(self, c: Class):
    if self.template_path != DEFAULT_TEMPLATE_PATH:
      raise Exception()
    anchor, *names = self.template_path.split(".")
    with path(anchor, *names) as p:
      env = Environment(loader=FileSystemLoader(str(p)))
      template = env.get_template("ClassCPP_.j2")

      includes = OrderedSet[str]()
      for m in c.functions(EXPORT_SETTINGS_CLASS_INCLUDE):
        includes += list(m.includes(EXPORT_SETTINGS_CLASS_INCLUDE))

      methods = [{
        "returnType": f.f.properties.additionalProperties.ret.typeName, 
        "name": f.name.split("::")[-1], # split if necessary (mistake in export)
        "parameters": [f"{param.typeName} {param.name}" for param in f.f.properties.additionalProperties.params if param.name != "this"],
        "parameter_names": [f"{param.name}" for param in f.f.properties.additionalProperties.params if param.name != "this"],
        "address": f.f.locations[0].physicalLocation.address.absoluteAddress,
      } for f in c.functions(EXPORT_SETTINGS_CLASS_INCLUDE)]

      contents = template.render({
        "context": self.binary_context,
        "include_paths": sorted(includes) + [
           f"{c.location(ctx=EXPORT_SETTINGS_CLASS_INCLUDE)}/{c.name}Namespace.h",
           f"{c.location(ctx=EXPORT_SETTINGS_CLASS_INCLUDE)}/{c.name}Class_.h",
        ],
        "using_paths": sorted(includes),
        "namespace_path": c.namespace(ctx=EXPORT_SETTINGS_CLASS_INCLUDE),
        "class_name": f"{c.name}Class",
        "class_size": c.structure.s.properties.additionalProperties.size,
        "methods": methods,
        "singleton_address": c.singleton.defined_data.address() if c.singleton else 0,
      })

      return ExportContents(path=f"{c.location(ctx=EXPORT_SETTINGS_CLASS_INCLUDE)}/{c.name}Class_.cpp", contents=contents)
    
  def export_class_namespace(self, c: Class):
    if self.template_path != DEFAULT_TEMPLATE_PATH:
      raise Exception()
    anchor, *names = self.template_path.split(".")
    with path(anchor, *names) as p:
      env = Environment(loader=FileSystemLoader(str(p)))
      template = env.get_template("ClassNamespaceH.j2")

      includes = OrderedSet[str]()
      for m in c.functions(EXPORT_SETTINGS_CLASS_INCLUDE):
        includes += list(m.includes(EXPORT_SETTINGS_CLASS_INCLUDE))

      methods = [{
        "returnType": f.f.properties.additionalProperties.ret.typeName, 
        "name": f.name.split("::")[-1], # split if necessary (mistake in export)
        "parameters": [f"{param.typeName} {param.name}" for param in f.f.properties.additionalProperties.params if param.name != "this"],
        "address": f.f.locations[0].physicalLocation.address.absoluteAddress,
      } for f in c.functions(EXPORT_SETTINGS_CLASS_INCLUDE)]

      contents = template.render({
        "use_pch": True,
        "context": self.binary_context,
        "include_paths": sorted(includes) + [
          f"{c.location(ctx=EXPORT_SETTINGS_CLASS_INCLUDE)}/{c.name}Class.h",
        ],
        "using_paths": sorted(includes),
        "namespace_path": c.namespace(ctx=EXPORT_SETTINGS_CLASS_INCLUDE),
        "class_name": f"{c.name}Class",
        "class_size": c.structure.s.properties.additionalProperties.size,
        "methods": methods,
        "singleton_name": f"DAT_{c.name}", # TODO: probably almost always correct?
      })

      return ExportContents(path=f"{c.location(ctx=EXPORT_SETTINGS_CLASS_INCLUDE)}/{c.name}Namespace.h", contents=contents)

  def export_class_namespace_helper(self, c: Class):
    if self.template_path != DEFAULT_TEMPLATE_PATH:
      raise Exception()
    anchor, *names = self.template_path.split(".")
    with path(anchor, *names) as p:
      env = Environment(loader=FileSystemLoader(str(p)))
      template = env.get_template("IncludesOnlyH.j2")

      includes = [f"{c.location(ctx=EXPORT_SETTINGS_CLASS_INCLUDE)}.h"]
      contents = template.render({
        "use_pch": True,
        "include_paths": includes,
      })

      return ExportContents(path=f"{c.location(ctx=EXPORT_SETTINGS_CLASS_INCLUDE)}.h", contents=contents)
    
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

      includes = OrderedSet(s.includes(EXPORT_SETTINGS_CLASS_INCLUDE))

      fields =  list({"string": s, "offset": o, "length": l} for s, o, l in s.export_field_declarations_with_offsets_and_lengths(EXPORT_SETTINGS_CLASS_INCLUDE))
      
      contents = template.render({
        "use_pch": True,
        "include_paths": sorted(includes),
        "using_paths": sorted(includes),
        "namespace_path": s.namespace(ctx=EXPORT_SETTINGS_CLASS_INCLUDE),
        "struct_name": s.name,
        "struct_size": s.s.properties.additionalProperties.size,
        "fields": fields,
      })
    
      return ExportContents(path=f"{s.location(ctx=EXPORT_SETTINGS_CLASS_INCLUDE)}/{s.name}.h", contents=contents)

  def export_enum(self, e: Enum):
    if self.template_path != DEFAULT_TEMPLATE_PATH:
      raise Exception()
    anchor, *names = self.template_path.split(".")
    with path(anchor, *names) as p:
      env = Environment(loader=FileSystemLoader(str(p)))
      template1 = env.get_template("EnumH.j2")

      namespace_path = e.namespace(ctx=EXPORT_SETTINGS_CLASS_INCLUDE)

      fields = [{"name": key, "value": value} for key, value in e.er.properties.additionalProperties.constants.items()]
      name = e.er.properties.additionalProperties.name
      type = e.er.properties.additionalProperties.base
      contents = template1.render({
        "use_pch": True,
        "namespace_path": namespace_path,
        "name": name,
        "type": type,
        "fields": fields,
      })
      return ExportContents(path=f"{e.location(ctx=EXPORT_SETTINGS_CLASS_INCLUDE)}/{e.name}.h", contents=contents)


  def export_sized_enum(self, e: Enum) -> List[ExportContents]:
    if self.template_path != DEFAULT_TEMPLATE_PATH:
      raise Exception()
    anchor, *names = self.template_path.split(".")
    with path(anchor, *names) as p:
      env = Environment(loader=FileSystemLoader(str(p)))
      template1 = env.get_template("SizedEnum_CPP03_H.j2")
      template2 = env.get_template("SizedEnum_CPP03_CPP.j2")

      namespace_path = e.namespace(ctx=EXPORT_SETTINGS_CLASS_INCLUDE)

      fields = [{"name": key, "value": value} for key, value in e.er.properties.additionalProperties.constants.items()]
      name = e.er.properties.additionalProperties.name
      type = e.er.properties.additionalProperties.base
      path1 = f"{e.location(ctx=EXPORT_SETTINGS_CLASS_INCLUDE)}/{e.name}.h"
      contents1 = template1.render({
        "use_pch": True,
        "namespace_path": namespace_path,
        "name": name,
        "type": type,
        "fields": fields,
      })

      path2 = f"{e.location(ctx=EXPORT_SETTINGS_CLASS_INCLUDE)}/{e.name}.cpp"
      contents2 = template2.render({
        "include_paths": [path1],
        "namespace_path": namespace_path,
        "name": name,
        "type": type,
        "fields": fields,
      })

      return [ExportContents(path=path1, contents=contents1), ExportContents(path=path2, contents=contents2)]