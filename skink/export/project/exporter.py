from jinja2 import Environment, FileSystemLoader
from importlib.resources import path

from skink.architecture.classes.cls import Class
from skink.architecture.structs.struct import Struct
from skink.utils.OrderedSet import OrderedSet
from skink.export.context import DEFAULT, Context

from dataclasses import dataclass
from dataclasses_json import dataclass_json

DEFAULT_TEMPLATE_PATH = "skink.export.templates"
EXPORT_SETTINGS_CLASS_INCLUDE: Context = DEFAULT.copy()
EXPORT_SETTINGS_CLASS_INCLUDE.include = EXPORT_SETTINGS_CLASS_INCLUDE.include.mutate(functions_this_parameter_type=False, prefix_include=False)
EXPORT_SETTINGS_CLASS_INCLUDE.struct_rules = EXPORT_SETTINGS_CLASS_INCLUDE.struct_rules.mutate(field_eol_char = False)
EXPORT_SETTINGS_CLASS_INCLUDE.location_rules = EXPORT_SETTINGS_CLASS_INCLUDE.location_rules.mutate(transformation_rules = EXPORT_SETTINGS_CLASS_INCLUDE.location_rules.transformation_rules.mutate(use_regex = True, regex={"_HoldStrong": "EXE"}))

EXPORT_SETTINGS_CLASS_SHIM_FILENAME = DEFAULT.copy()
EXPORT_SETTINGS_CLASS_SHIM_FILENAME.class_rules = EXPORT_SETTINGS_CLASS_SHIM_FILENAME.class_rules.mutate(suffix = "_")
EXPORT_SETTINGS_CLASS_SHIM_FILENAME.location_rules = EXPORT_SETTINGS_CLASS_SHIM_FILENAME.location_rules.mutate(transformation_rules = EXPORT_SETTINGS_CLASS_SHIM_FILENAME.location_rules.transformation_rules.mutate(use_regex = True, regex={"_HoldStrong": "EXE"}))


@dataclass
@dataclass_json
class BinaryContext:
  hash: str = "3bb0a8c1"
  abbreviation: str = "shc"

@dataclass
class ExportContents:
  path: str
  contents: str

  def __repr__(self) -> str:
    return f"/**\n  AUTO_GENERATED: DO NOT TOUCH THIS FILE\n  path: '{self.path}'\n*/\n\n{self.contents}"

DEFAULT_BINARY_CONTEXT: BinaryContext = BinaryContext()

class Exporter(object):
  
  def __init__(self, template_path: str = DEFAULT_TEMPLATE_PATH, binary_context: BinaryContext = DEFAULT_BINARY_CONTEXT):
    self.template_path = template_path
    self.binary_context = binary_context

  def export_class_header(self, c: Class):
    if self.template_path != DEFAULT_TEMPLATE_PATH:
      raise Exception()
    anchor, *names = self.template_path.split(".")
    with path(anchor, *names) as p:
      env = Environment(loader=FileSystemLoader(str(p)))
      template = env.get_template("ClassH.j2")

      includes = OrderedSet()
      for m in c.fs:
        includes += list(m.includes(EXPORT_SETTINGS_CLASS_INCLUDE))

      methods = [{
        "returnType": f.f.properties.additionalProperties.ret.typeName, 
        "name": f.name.split("::")[-1], # split if necessary (mistake in export)
        "parameters": [f"{param.typeName} {param.name}" for param in f.f.properties.additionalProperties.params if param.name != "this"],
      } for f in c.fs]

      contents = template.render({
        "include_paths": sorted(includes),
        "namespace_path": c.namespace(ctx=EXPORT_SETTINGS_CLASS_INCLUDE),
        "class_name": f"{c.name}Class",
        "class_size": c.structure.s.properties.additionalProperties.size,
        "methods": methods,
      })

      return ExportContents(path=f"{c.location(ctx=EXPORT_SETTINGS_CLASS_INCLUDE)}/{c.name}Class.h", contents=contents)
    
  def export_class_header_shim(self, c: Class):
    if self.template_path != DEFAULT_TEMPLATE_PATH:
      raise Exception()
    anchor, *names = self.template_path.split(".")
    with path(anchor, *names) as p:

      includes = OrderedSet()
      for m in c.fs:
        includes += list(m.includes(EXPORT_SETTINGS_CLASS_INCLUDE))

      methods = [{
        "returnType": f.f.properties.additionalProperties.ret.typeName, 
        "name": f.name.split("::")[-1], # split if necessary (mistake in export)
        "parameters": [f"{param.typeName} {param.name}" for param in f.f.properties.additionalProperties.params if param.name != "this"],
      } for f in c.fs]

      env = Environment(loader=FileSystemLoader(str(p)))
      template = env.get_template("ClassH_.j2")

      contents = template.render({
        "include_paths": sorted(includes),
        "namespace_path": c.namespace(ctx=EXPORT_SETTINGS_CLASS_INCLUDE),
        "class_name": f"{c.name}Class",
        "class_size": c.structure.s.properties.additionalProperties.size,
        "methods": methods,
      })

      return ExportContents(path=f"{c.location(ctx=EXPORT_SETTINGS_CLASS_INCLUDE)}/{c.name}Class_.h", contents=contents)

  def export_struct_header_for_class(self, c: Class):
    if self.template_path != DEFAULT_TEMPLATE_PATH:
      raise Exception()
    anchor, *names = self.template_path.split(".")
    with path(anchor, *names) as p:
      s: Struct = c.structure
      env = Environment(loader=FileSystemLoader(str(p)))
      template = env.get_template("StructH.j2")

      includes = OrderedSet(s.includes(EXPORT_SETTINGS_CLASS_INCLUDE))

      fields =  list(s.export_field_declarations(EXPORT_SETTINGS_CLASS_INCLUDE))
      
      contents = template.render({
        "include_paths": sorted(includes),
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

      includes = OrderedSet()
      for m in c.fs:
        includes += list(m.includes(EXPORT_SETTINGS_CLASS_INCLUDE))

      methods = [{
        "returnType": f.f.properties.additionalProperties.ret.typeName, 
        "name": f.name.split("::")[-1], # split if necessary (mistake in export)
        "parameters": [f"{param.typeName} {param.name}" for param in f.f.properties.additionalProperties.params if param.name != "this"],
        "address": f.f.locations[0].physicalLocation.address.absoluteAddress,
      } for f in c.fs]

      contents = template.render({
        "context": self.binary_context,
        "include_paths": sorted(includes),
        "namespace_path": c.namespace(ctx=EXPORT_SETTINGS_CLASS_INCLUDE),
        "class_name": f"{c.name}Class",
        "class_size": c.structure.s.properties.additionalProperties.size,
        "methods": methods,
      })

      return ExportContents(path=f"{c.location(ctx=EXPORT_SETTINGS_CLASS_INCLUDE)}/{c.name}Class.cpp", contents=contents)

  def export_class_body_shim(self, c: Class):
    if self.template_path != DEFAULT_TEMPLATE_PATH:
      raise Exception()
    anchor, *names = self.template_path.split(".")
    with path(anchor, *names) as p:
      env = Environment(loader=FileSystemLoader(str(p)))
      template = env.get_template("ClassCPP_.j2")

      includes = OrderedSet()
      for m in c.fs:
        includes += list(m.includes(EXPORT_SETTINGS_CLASS_INCLUDE))

      methods = [{
        "returnType": f.f.properties.additionalProperties.ret.typeName, 
        "name": f.name.split("::")[-1], # split if necessary (mistake in export)
        "parameters": [f"{param.typeName} {param.name}" for param in f.f.properties.additionalProperties.params if param.name != "this"],
        "address": f.f.locations[0].physicalLocation.address.absoluteAddress,
      } for f in c.fs]

      contents = template.render({
        "context": self.binary_context,
        "include_paths": sorted(includes),
        "namespace_path": c.namespace(ctx=EXPORT_SETTINGS_CLASS_INCLUDE),
        "class_name": f"{c.name}Class",
        "class_size": c.structure.s.properties.additionalProperties.size,
        "methods": methods,
      })

      return ExportContents(path=f"{c.location(ctx=EXPORT_SETTINGS_CLASS_INCLUDE)}/{c.name}Class_.cpp", contents=contents)
    
  def export_namespace_for_class(self, c: Class):
    if self.template_path != DEFAULT_TEMPLATE_PATH:
      raise Exception()
    anchor, *names = self.template_path.split(".")
    with path(anchor, *names) as p:
      env = Environment(loader=FileSystemLoader(str(p)))
      template = env.get_template("NamespaceH.j2")

      includes = OrderedSet()
      for m in c.fs:
        includes += list(m.includes(EXPORT_SETTINGS_CLASS_INCLUDE))

      methods = [{
        "returnType": f.f.properties.additionalProperties.ret.typeName, 
        "name": f.name.split("::")[-1], # split if necessary (mistake in export)
        "parameters": [f"{param.typeName} {param.name}" for param in f.f.properties.additionalProperties.params if param.name != "this"],
        "address": f.f.locations[0].physicalLocation.address.absoluteAddress,
      } for f in c.fs]

      contents = template.render({
        "context": self.binary_context,
        "include_paths": sorted(includes),
        "namespace_path": c.namespace(ctx=EXPORT_SETTINGS_CLASS_INCLUDE),
        "class_name": f"{c.name}Class",
        "class_size": c.structure.s.properties.additionalProperties.size,
        "methods": methods,
        "singleton_name": f"DAT_{c.name}", # TODO: probably almost always correct?
      })

      return ExportContents(path=f"{c.location(ctx=EXPORT_SETTINGS_CLASS_INCLUDE)}/{c.name}Namespace.h", contents=contents)