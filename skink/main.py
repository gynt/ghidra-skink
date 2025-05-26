import argparse
import pathlib
import sys
import os

from skink.cli.create import main_create
from skink.cli.export import main_export
from skink.cli.settings import main_settings
from skink.cli.preprocess import main_preprocess
from skink.export.project.project import Project

parser = argparse.ArgumentParser(prog="skink", add_help=True)
parser.add_argument("--debug", required=False, default=False, action='store_true')
parser.add_argument("--verbose", required=False, default=False, action='store_true')
subparsers = parser.add_subparsers(title="subcommands", required=True, dest='subcommand')

preprocess = subparsers.add_parser('preprocess')
preprocess.add_argument("file", nargs=1, help="sarif file to preprocess")
preprocess.add_argument("--filter-namespace", type=str, default="", required=False)
preprocess.add_argument("--output", default="preprocessed.json")

create = subparsers.add_parser('create')
create.add_argument("--dir", required=False, default=".", help="output directory (default: '.')")
create.add_argument("files", nargs='+', help="sarif files to be parsed and processed")
create.add_argument("--export", required=False, default="all", help='what to export (default "all")', choices=['all', 'classes', 'functions', 'structures', 'enums'])
create.add_argument("--limit", type=int, help="limit the export to this amount of entries (default: no limit)", default=0)
create.add_argument("--prefix", required=False, default="", help="filter sarif contents for namespaces with this prefix (default: '')")

export = subparsers.add_parser("export")
export.add_argument("what", choices=["*", "classes", "functions", "variables", "namespaces"])
export.add_argument("--input", required=True, help="input file")
export.add_argument("--output", required=False, default="output", help="outpath path")
export.add_argument("--input-format", default="sarif")

settings = subparsers.add_parser("settings")

def main_cli():
  args = parser.parse_args()

  if args.verbose or args.debug:
    print(f"Debug: {args}")

  print(f"Current directory: {os.getcwd()}")

  if args.subcommand == "create":
    return main_create(args)
  if args.subcommand == "preprocess":
    return main_preprocess(args)
  if args.subcommand == "export":
    return main_export(args)
  if args.subcommand == "settings":
    return main_settings(args)
  raise Exception(f"unimplemented subcommand {args.subcommand}")