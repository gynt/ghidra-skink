import json
import pathlib

from skink.logger import fatal
from skink.export.project.project import Project
from skink.sarif.decode_results import DECODE_RESULT_STATE, decode_result
from skink.sarif.importing.filters.namespaces import belongs_in_namespace
from ..logger import log, logging

def main_preprocess_filter(input_path, output_path, args):
  logic = 'and'
  if getattr(args, 'and'):
    if getattr(args, 'or'):
      fatal(f"Cannot set both AND and OR on a filter")
    logic = 'and'
  if getattr(args, 'or'):
    logic = 'or'

  log(logging.INFO, f"Applying filter: {logic}")
  nsf = args.filter_namespace
  if nsf:
    project = Project(path=input_path)

    l = list()
    with DECODE_RESULT_STATE as s:
      for a in project.yield_raw_objects():
        if args.debug:
          log(logging.DEBUG, a)
        obj = decode_result(a)
        if belongs_in_namespace(obj, nsf):
          l.append(a)
      output_path.write_text(json.dumps(l, indent=2))

def main_preprocess(args):
  path = pathlib.Path(args.file[0]).absolute()
  output_path = pathlib.Path(args.output).absolute()

  if output_path.exists():
    answer = input(f"Proceeding will overwrite the file '{output_path.name}'. Are you sure you want to continue? [y/n]")
    if answer not in "yY":
      return

  if args.action == 'filter':
    return main_preprocess_filter(path, output_path, args)
  raise Exception(f"preprocess: unhandled action: {args.action}")
