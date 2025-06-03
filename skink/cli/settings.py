import pathlib

from skink.export.context import DEFAULT
from ..logger import log, logging

def main_settings(args):
  settings_path = pathlib.Path("settings.json")
  if settings_path.exists() == False:
    settings_path.write_text(DEFAULT.to_json(indent=2)) # type: ignore
  else:
    if args.verbose or args.debug:
      log(logging.DEBUG, "settings.json already exists")