from jinja2 import Environment, FileSystemLoader

from typing import Dict

_environments: Dict[str, Environment] = {}

def template_environment(p) -> Environment:
  """
  Returns the jinja2 Environment for the template directory p.

  Environments are shared, so each template is compiled once instead of once per exported file.
  """
  key = str(p)
  env = _environments.get(key)
  if env is None:
    # Templates are package data, they do not change while exporting
    env = _environments[key] = Environment(loader=FileSystemLoader(key), auto_reload=False)
  return env
