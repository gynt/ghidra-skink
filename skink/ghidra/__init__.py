"""
Reads a program straight from Ghidra, through pyghidra, instead of from a SARIF export.

The records are the ones skink would decode from a SARIF export of the same program,
in the same order, so the exported headers are identical. Install with the ghidra extra
(pip install "skink[ghidra]") and set GHIDRA_INSTALL_DIR to a Ghidra installation.

  project = Project.from_gzf("program.gzf")

Modules that talk to Ghidra (extract) can only be imported once the JVM runs,
so they are imported inside the functions below.
"""

import pathlib
from typing import List

from skink.export.project.project import Record


def read_program(program) -> List[Record]:
  """Returns the records of a Ghidra Program, e.g. currentProgram in a pyghidra script."""
  from .extract import ProgramExtractor
  return list(ProgramExtractor(program).records())


def read_gzf(gzf: str | pathlib.Path) -> List[Record]:
  """Returns the records of the program packed in a Ghidra .gzf file, starting pyghidra when needed."""
  from .gzf import open_gzf
  with open_gzf(gzf) as program:
    return read_program(program)
