import os

from .args import parser
from skink.cli.create import main_create
from skink.cli.export import main_export
from skink.cli.sarif import main_sarif
from skink.cli.settings import main_settings
from skink.cli.preprocess import main_preprocess

from ..logger import log, logging

def main_cli():
  args = parser.parse_args()

  log(logging.INFO, f"Current directory: {os.getcwd()}")

  if args.verbose or args.debug:
    log(logging.DEBUG, f"Debug: {args}")

  

  if args.subcommand == "create":
    return main_create(args)
  if args.subcommand == "preprocess":
    return main_preprocess(args)
  if args.subcommand == "export":
    return main_export(args)
  if args.subcommand == "settings":
    return main_settings(args)
  if args.subcommand == "sarif":
    return main_sarif(args)
  raise Exception(f"unimplemented subcommand {args.subcommand}")