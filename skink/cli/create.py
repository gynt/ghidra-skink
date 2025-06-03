

import pathlib

from skink.export.project.project import Project
from ..logger import log, logging

def main_create(args):
  
  files = [pathlib.Path(fpath).absolute() for fpath in args.files]
  log(logging.DEBUG, "Files:")
  for fpath in files:
    log(logging.DEBUG, "  " + str(fpath))

  export_directory = pathlib.Path(args.dir).absolute()
  log(logging.DEBUG, f"Export directory: {export_directory}")

  log(logging.DEBUG, f"Exporting: {args.export}. Limit: {args.limit if args.limit > 0 else "no limit"}")
  project = Project(paths=files)

  log(logging.DEBUG, f"Importing sarif files")

  project.process_all_symbol_results(prefix = args.prefix, store_symbol_result = args.debug)
  log(logging.DEBUG, f"Total imported symbols: {project.counts['total']}")
  log(logging.DEBUG, project.counts)

  if args.debug:
    log(logging.DEBUG, "Debug: Dumping symbols")
    for k, v in project.symdb.db.items():
      log(logging.DEBUG, v)
  