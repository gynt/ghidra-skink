"""
Checks that reading a .gzf gives exactly the records skink decodes from a SARIF export of the same program.

Records are compared in order, field by field. Catch-all `extra` content and type `settings` are
ignored, since skink never reads them.

  skink ghidra verify --gzf program.gzf --sarif program.sarif
"""

import dataclasses
import itertools
import time

from skink.export.project.project import Project

IGNORED_FIELDS = {"extra", "settings"}


def plain(obj):
  if dataclasses.is_dataclass(obj):
    return {f.name: plain(getattr(obj, f.name)) for f in dataclasses.fields(obj) if f.name not in IGNORED_FIELDS}
  if isinstance(obj, list):
    return [plain(x) for x in obj]
  if isinstance(obj, dict):
    return {k: plain(v) for k, v in obj.items()}
  return obj


def differences(a, b, path=""):
  if type(a) != type(b):
    yield f"{path}: {a!r} != {b!r}"
  elif isinstance(a, dict):
    if list(a.keys()) != list(b.keys()):
      yield f"{path}: keys {list(a.keys())} != {list(b.keys())}"
    for k in a.keys() & b.keys():
      yield from differences(a[k], b[k], f"{path}.{k}")
  elif isinstance(a, list):
    if len(a) != len(b):
      yield f"{path}: length {len(a)} != {len(b)}"
    for i, (x, y) in enumerate(zip(a, b)):
      yield from differences(x, y, f"{path}[{i}]")
  elif a != b:
    yield f"{path}: {a!r} != {b!r}"


def verify(gzf, sarif, max_reports: int = 20) -> int:
  """Prints the differences between the records read from gzf and from sarif, returns how many records differ."""
  from skink.ghidra import read_gzf
  t = time.perf_counter()
  ours = read_gzf(gzf)
  print(f"read {len(ours)} records from {gzf} in {time.perf_counter() - t:.1f}s")

  t = time.perf_counter()
  theirs = Project(path=sarif).yield_records()
  reports = 0
  count = 0
  for i, (expected, actual) in enumerate(itertools.zip_longest(theirs, ours)):
    count += 1
    if expected is None or actual is None:
      print(f"record {i}: only in {'gzf' if expected is None else 'sarif'}: {(expected or actual)[:2]}")
      reports += 1
    else:
      diffs = list(differences(plain(expected[2]), plain(actual[2])))
      if expected[:2] != actual[:2] or diffs:
        reports += 1
        print(f"record {i} {expected[:2]} vs {actual[:2]}:")
        for d in diffs[:10]:
          print(f"  {d}")
    if reports >= max_reports:
      print("too many differences, stopping")
      break
  print(f"compared {count} records in {time.perf_counter() - t:.1f}s: {'IDENTICAL' if reports == 0 else f'{reports} DIFFERENT'}")
  return reports
