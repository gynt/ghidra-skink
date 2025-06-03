import logging

def log(level, msg, *args, **kwargs):
    return logging.log(level=level, msg=msg, *args, **kwargs)

def test_logger():
    log(logging.INFO, f"Logger set to level: {logging.getLogger().level} ({logging.getLevelName(logging.getLogger().level)})")