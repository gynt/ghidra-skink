import os

from skink.export.project.project import log_ijson_backend

from .args import parser
from skink.cli.create import main_create
from skink.cli.export import main_export
from skink.cli.sarif import main_sarif
from skink.cli.settings import main_settings
from skink.cli.preprocess import main_preprocess

from ..logger import log, logging, setup_logger, test_logger

def main_cli():
  args = parser.parse_args()

  setup_logger(include_console=args.log_console, include_file=args.log_file, console_stderr=args.log_console_to_stderr, silent=args.silent)

  log(logging.INFO, f"Current directory: {os.getcwd()}")

  if args.verbose or args.debug:
    test_logger()
    log(logging.DEBUG, f"Debug: {args}")
    log_ijson_backend()
  

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