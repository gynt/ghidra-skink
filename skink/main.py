import argparse
import pathlib
import sys
import os

from skink.export.project.project import Project

parser = argparse.ArgumentParser(prog="skink", add_help=True)
parser.add_argument("--dir", required=False, default=".", help="output directory (default: '.')")
parser.add_argument("files", nargs='+', help="sarif files to be parsed and processed")
parser.add_argument("--export", required=False, default="all", help='what to export (default "all")', choices=['all', 'classes', 'functions', 'structures', 'enums'])
parser.add_argument("--limit", type=int, help="limit the export to this amount of entries (default: no limit)", default=0)
parser.add_argument("--prefix", required=False, default="", help="filter sarif contents for namespaces with this prefix (default: '')")
parser.add_argument("--debug", required=False, default=False, action='store_true')
parser.add_argument("--verbose", required=False, default=False, action='store_true')

def main_cli():
  args = parser.parse_args()

  if args.verbose or args.debug:
    print(f"Debug: {args}")

  print(f"Current directory: {os.getcwd()}")

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
  