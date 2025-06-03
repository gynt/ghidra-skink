from .logger import *
from yaml import safe_load
from pathlib import Path
import logging.config
import sys

with Path('logging.yml').open() as f:
    logging.config.dictConfig(safe_load(f))

test_logger()

def fatal(reason):
    log(logging.FATAL, reason)
    sys.exit(1)