import sys

import logging

import importlib.resources

from yaml import safe_load
import logging.config

def setup_logger(include_file = True, include_console = True):
  with importlib.resources.open_text('skink', 'logging.yml') as f:
    logging.config.dictConfig(safe_load(f))
  l = logging.getLogger()
  # Remove handlers for file and console if desired.
  if not include_file and not include_console:
    raise Exception(f"Logging disabled. This is not what you want.")
  if not include_file:
    l.handlers = [h for h in l.handlers if not h._name == "file"]
  if not include_console:
    l.handlers = [h for h in l.handlers if not h._name == "console"]

def log(level, msg, *args, **kwargs):
  return logging.log(level=level, msg=msg, *args, **kwargs)

def test_logger():
  log(logging.INFO, f"Logger set to level: {logging.getLogger().level} ({logging.getLevelName(logging.getLogger().level)})")

def fatal(reason):
  log(logging.FATAL, reason)
  sys.exit(1)