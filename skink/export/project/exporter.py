from jinja2 import Environment, FileSystemLoader
from importlib.resources import path

from skink.architecture.classes.cls import Class

DEFAULT_TEMPLATE_PATH = "skink.export.templates"

class Exporter(object):
  
  def __init__(self, template_path: str = DEFAULT_TEMPLATE_PATH):
    self.template_path = template_path

  def export_class_header(self, c: Class):
    if self.template_path != DEFAULT_TEMPLATE_PATH:
      raise Exception()
    anchor, *names = self.template_path.split(".")
    with path(anchor, *names) as p:
      env = Environment(loader=FileSystemLoader(str(p)))
      template = env.get_template("ClassH.j2")

      methods = [{
        "returnType": f.f.properties.additionalProperties.ret.typeName, 
        "name": f.name.split("::")[-1], # split if necessary (mistake in export)
        "parameters": [f"{param.typeName} {param.name}" for param in f.f.properties.additionalProperties.params if param.name != "this"],
      } for f in c.fs]

      return template.render({
        "namespace_path": c.ns,
        "class_name": c.name,
        "class_size": c.structure.s.properties.additionalProperties.size,
        "methods": methods,
      })
