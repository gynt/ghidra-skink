

import pathlib

from skink.export.project.project import Project


def main_create(args):
  
  files = [pathlib.Path(fpath).absolute() for fpath in args.files]
  print("Files:")
  for fpath in files:
    print("  " + str(fpath))

  export_directory = pathlib.Path(args.dir).absolute()
  print(f"Export directory: {export_directory}")

  print(f"Exporting: {args.export}. Limit: {args.limit if args.limit > 0 else "no limit"}")
  project = Project(paths=files)

  print(f"Importing sarif files")

  project.process_all_symbol_results(prefix = args.prefix, store_symbol_result = args.debug)
  print(f"Total imported symbols: {project.counts['total']}")
  print(project.counts)

  if args.debug:
    print("Debug: Dumping symbols")
    for k, v in project.symdb.db.items():
      print(v)
  