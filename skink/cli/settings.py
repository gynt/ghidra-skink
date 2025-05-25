import pathlib

from skink.export.context import DEFAULT


def main_options(args):
  settings_path = pathlib.Path("settings.json")
  if settings_path.exists() == False:
    settings_path.write_text(DEFAULT.to_json(indent=2))