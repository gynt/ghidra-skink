"""
Opening a program from a Ghidra .gzf file with pyghidra.
"""

import contextlib
import logging
import pathlib
import shutil
import tempfile
import time
from typing import Generator

log = logging.getLogger(__name__)


def start():
  import pyghidra
  if not pyghidra.started():
    t = time.perf_counter()
    pyghidra.start()
    log.info(f"started pyghidra in {time.perf_counter() - t:.1f}s")


@contextlib.contextmanager
def open_gzf(gzf: str | pathlib.Path) -> Generator:
  """
  Yields the (read-only) Program packed in a .gzf file.

  The gzf is opened directly as a packed database. If that is not possible (for
  example when the gzf was made by an older Ghidra and needs an upgrade), the gzf
  is imported into a throwaway Ghidra project instead.
  """
  start()
  from ghidra.util.exception import VersionException  # type: ignore

  gzf = pathlib.Path(gzf).absolute()
  if not gzf.exists():
    raise FileNotFoundError(gzf)

  t = time.perf_counter()
  with contextlib.ExitStack() as stack:
    try:
      program = stack.enter_context(_open_packed(gzf))
    except VersionException as e:
      log.info(f"cannot open {gzf.name} directly ({e}), importing it into a temporary project")
      program = stack.enter_context(_open_imported(gzf))
    log.info(f"opened {gzf.name} in {time.perf_counter() - t:.1f}s")
    yield program


@contextlib.contextmanager
def _open_packed(gzf: pathlib.Path) -> Generator:
  from java.io import File  # type: ignore
  from java.lang import Object  # type: ignore
  from ghidra.framework.data import OpenMode  # type: ignore
  from ghidra.framework.store.db import PackedDatabase  # type: ignore
  from ghidra.program.database import ProgramDB  # type: ignore
  from ghidra.program.model.data import BuiltInDataTypeManager  # type: ignore
  from ghidra.util.task import TaskMonitor  # type: ignore

  # Built-in data types (e.g. ImageBaseOffset32) are resolved through the built-in data type manager.
  # Importing initializes it; opening the database directly does not, and they would come out as -MISSING-.
  BuiltInDataTypeManager.getDataTypeManager()

  packed = PackedDatabase.getPackedDatabase(File(str(gzf)), True, TaskMonitor.DUMMY)
  try:
    handle = packed.open(TaskMonitor.DUMMY)
    consumer = Object()
    program = ProgramDB(handle, OpenMode.IMMUTABLE, TaskMonitor.DUMMY, consumer)
    try:
      yield program
    finally:
      program.release(consumer)
  finally:
    packed.dispose()


@contextlib.contextmanager
def _open_imported(gzf: pathlib.Path) -> Generator:
  import pyghidra

  project_dir = tempfile.mkdtemp(prefix="skink-")
  project = pyghidra.open_project(project_dir, "skink", create=True)
  try:
    with pyghidra.program_loader().project(project).source(str(gzf)).load() as load_results:
      load_results.save(pyghidra.task_monitor())
    files = project.getProjectData().getRootFolder().getFiles()
    if len(files) != 1:
      raise Exception(f"expected one program in {gzf.name}, found: {[f.getPathname() for f in files]}")
    program, consumer = pyghidra.consume_program(project, files[0].getPathname())
    try:
      yield program
    finally:
      program.release(consumer)
  finally:
    project.close()
    shutil.rmtree(project_dir, ignore_errors=True)
