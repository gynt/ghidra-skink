

import json
import pathlib
import pathvalidate

from skink.export.location import normalize_location
from skink.export.project.project import Project
from skink.sarif.datatypes.DataTypeResult import DataTypeResult
from skink.sarif.decode_results import decode_results
from skink.sarif.functions.FunctionResult import FunctionResult
from skink.sarif.symbols.symbol import SymbolResult
from ..logger import log, logging

def write_obj(fname, fpath):
  pass

def main_sarif(args):
  if args.sarif_action != "extract":
    raise Exception(f"not implemented: {args.sarif_action}")
  o = pathlib.Path(args.output)
  if not o.exists():
    o.mkdir(parents = True)

  input_path = pathlib.Path(args.input)
  if args.input_format == "sarif":
    project = Project(path=input_path)
  else:
    raw_objs = json.loads(input_path.read_text())
    project = Project(objects = raw_objs)

  for obj in project.yield_objects(debug=args.debug):
    if args.debug:
      log(logging.DEBUG, obj)
    if isinstance(obj, FunctionResult):
      fr: FunctionResult = obj
      ns = fr.properties.additionalProperties.namespace
      loc = normalize_location(ns.replace("::", "/"))
      name = fr.properties.additionalProperties.name
      cloc = f"{loc}/{name}"
      loc = pathvalidate.sanitize_filepath(cloc, "_", pathvalidate.Platform.UNIVERSAL)
      if not loc:
        raise Exception(cloc)
      d = o / pathlib.Path(loc)
      d.mkdir(parents = True, exist_ok = True)
      (d / "function.json").write_text(obj.to_json(indent = 2)) # type: ignore
    if isinstance(obj, DataTypeResult):
      dtr: DataTypeResult = obj
      ns = dtr.properties.additionalProperties.location
      loc = normalize_location(ns.replace("::", "/"))
      name = dtr.properties.additionalProperties.name
      cloc = f"{loc}/{name}"
      loc = pathvalidate.sanitize_filepath(cloc, "_", pathvalidate.Platform.UNIVERSAL)
      if not loc:
        raise Exception(cloc)
      d = o / pathlib.Path(loc)
      d.mkdir(parents = True, exist_ok = True)
      (d / "datatype.json").write_text(obj.to_json(indent = 2)) # type: ignore
    if isinstance(obj, SymbolResult):
      sr: SymbolResult = obj
      ns = sr.properties.additionalProperties.location
      loc = normalize_location(ns.replace("::", "/"))
      name = sr.properties.additionalProperties.name
      cloc = f"{loc}{name}"
      loc = pathvalidate.sanitize_filepath(cloc, "_", pathvalidate.Platform.UNIVERSAL)
      if not loc:
        raise Exception(cloc)
      d = o / pathlib.Path(loc)
      d.mkdir(parents = True, exist_ok = True)
      (d / "symbol.json").write_text(obj.to_json(indent = 2)) # type: ignore