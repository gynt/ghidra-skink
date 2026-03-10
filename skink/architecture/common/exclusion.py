


from typing import Iterable
from skink.export.context import Context

import re

def filter_includes(includes: Iterable[str], ctx: Context):
  for include in includes:
    inc = True
    for pattern in ctx.include.exclude:
      if ctx.include.exclude_use_regex:
        if re.match(pattern, include):
          inc = False
    if inc:
      for needle, replacement in ctx.include.remap:
        include = re.sub(needle, replacement, include)
      yield include

