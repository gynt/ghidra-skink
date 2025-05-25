import json
import pathlib

from skink.export.project.project import Project
from skink.sarif.decode_results import decode_result
from skink.sarif.importing.filters.namespaces import belongs_in_namespace

def main_preprocess(args):
  path = pathlib.Path(args.file[0]).absolute()
  output_path = pathlib.Path(args.output).absolute()
  nsf = args.filter_namespace

  if nsf:
    project = Project(path=path)

    l = list()
    for a in project.yield_objects():
      if args.debug:
        print(a)
      obj = decode_result(a)
      if belongs_in_namespace(obj, nsf):
        l.append(a)
    output_path.write_text(json.dumps(l, indent=2))
