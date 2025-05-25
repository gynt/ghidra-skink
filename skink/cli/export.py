import json
import pathlib

from skink.export.classes.collect import collect_classes
from skink.export.context import DEFAULT, Context
from skink.export.project.project import Project
from skink.sarif.decode_results import decode_results


def main_export(args):
  input_path = pathlib.Path(args.input).absolute()
  output_path = pathlib.Path(args.output).absolute()

  settings_path = pathlib.Path("settings.json")
  ctx = DEFAULT
  if settings_path.exists():
    ctx = Context.from_json(settings_path.read_text())

  if args.input_format == "sarif":
    project = Project(path=input_path)
  else:
    raw_objs = json.loads(input_path.read_text())
    project = Project(objects = decode_results(raw_objs))

  if "classes" in args.what:
    results = list(project.yield_objects())
    if args.debug:
      print(len(results))
      a = list(collect_classes(results))
      print(len(a))
      for cls in a:
        print(cls.export(ctx))
  else:
    raise Exception(args)