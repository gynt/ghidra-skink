


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
      yield include