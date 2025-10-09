import logging
import pathlib
from typing import Dict
from skink.export.project.exportcontents import ExportContents


class ExportedContentCollection(object):

  def __init__(self):
    self.db: Dict[str, ExportContents] = {}
    self.stubs: Dict[str, bool] = {}

  def add(self, *contents: ExportContents):
    for content in contents:
      if content.path in self.db:
        raise Exception(f"already in collection: {content.path}")
      self.db[content.path] = content

  def stub(self, path: str):
    if path in self.stubs:
      if not self.stubs[path]:
        return # nothing to be done here, stub was resolved
    if path in self.db:
      return # stub was resolved
    self.stubs[path] = True

  def unresolved_stubs(self):
    return [path for path, stubbed in self.stubs.items() if stubbed]
  
  def write_to_disk(self, base: pathlib.Path):
    stbs = self.unresolved_stubs()
    if len(stbs) > 0:
      logging.log(logging.WARNING, f"there are {len(stbs)} unresolved paths")
    for path, contents in self.db.items():
      p: pathlib.Path = base / path
      p.parent.mkdir(parents=True, exist_ok=True)
      p.write_text(contents.contents)