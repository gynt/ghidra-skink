import sys

import logging

import importlib.resources

from yaml import safe_load
import logging.config

def setup_logger(include_file = True, include_console = True, console_stderr = False, silent=False):
  with importlib.resources.open_text('skink', 'logging.yml') as f:
    logging.config.dictConfig(safe_load(f))
  l = logging.getLogger()
  # Remove handlers for file and console if desired.
  if silent:
    logging.disable(logging.CRITICAL)
    return
  if not include_file:
    l.handlers = [h for h in l.handlers if not h.name == "file"]
  if not include_console:
    if console_stderr:
      raise Exception(f"incompatible logging options")
    l.handlers = [h for h in l.handlers if not h.name == "console"]
  if console_stderr:
    hs = [h for h in l.handlers if h.name == "console"]
    if len(hs) != 1:
      raise Exception("incompatible logging options")
    h = hs[0]
    if not isinstance(h, logging.StreamHandler):
      raise Exception("logging handler not a StreamHandler")
    h.setStream(sys.stderr)


def log(level, msg, *args, **kwargs):
  return logging.log(level=level, msg=msg, *args, **kwargs)

def test_logger():
  log(logging.INFO, f"Logger set to level: {logging.getLogger().level} ({logging.getLevelName(logging.getLogger().level)})")

def fatal(reason):
  log(logging.FATAL, reason)
  sys.exit(1)