import sys

import logging

import importlib.resources

from yaml import safe_load
import logging.config

with importlib.resources.open_text('skink', 'logging.yml') as f:
    logging.config.dictConfig(safe_load(f))

def log(level, msg, *args, **kwargs):
    return logging.log(level=level, msg=msg, *args, **kwargs)

def test_logger():
    log(logging.INFO, f"Logger set to level: {logging.getLogger().level} ({logging.getLevelName(logging.getLogger().level)})")

def fatal(reason):
    log(logging.FATAL, reason)
    sys.exit(1)