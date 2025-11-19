import logging
import pathlib
from typing import Dict
from skink.export.project.exportcontents import ExportContents
import pathvalidate

class ExportedContentCollection(object):

  def __init__(self, ignore_duplicates: bool = False):
    self.db: Dict[str, ExportContents] = {}
    self.stubs: Dict[str, bool] = {}
    self.ignore_duplicates: bool = ignore_duplicates

  def add(self, *contents: ExportContents):
    for content in contents:
      if content.path in self.db:
        if content.contents != self.db[content.path].contents:
          if not self.ignore_duplicates:
            raise Exception(f"already in collection and different: {content.path}")
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
  
  def write_to_disk(self, base: pathlib.Path, overwrite_all=False):
    stbs = self.unresolved_stubs()
    if len(stbs) > 0:
      logging.log(logging.WARNING, f"there are {len(stbs)} unresolved paths")
    for path, contents in self.db.items():
      p: pathlib.Path = base / path
      if not pathvalidate.is_valid_filepath(p):
        logging.log(logging.WARNING, f"invalid path name, skipping: {str(p)}")
        continue
      p.parent.mkdir(parents=True, exist_ok=True)
      if not overwrite_all and (not contents.no_touch and p.exists()):
        continue
      p.write_text(str(contents))