
from dataclasses import dataclass
from typing import Any, Dict, Generator, List

from skink.sarif.symbols.symbol import SymbolResult


def sanitize(path):
  return path.replace("?", "")


@dataclass
class SymbolEntry:
  path: str
  kind: str # 'class' | 'namespace' | 'function' | 'data' | 'member'
  address: int = 0
  external: bool = False
  extra: Any = None


class SymbolDatabase(object):

  def __init__(self, sanitize = True):
    self.db: Dict[str, SymbolEntry] = {}
    self.address_db: Dict[int, List[SymbolEntry]] = {}
    self.sanitize: bool = sanitize

  def by_address(self, address) -> Generator[SymbolEntry]:
    if address not in self.address_db:
      raise Exception(f"address not in database: {address}")
    yield from self.address_db[address]

  def get(self, key) -> SymbolEntry:
    if self.sanitize:
      key = sanitize(key)
    if key in self.db:
      return self.db[key]
    raise Exception(f"no such key: {key}")
  
  def set(self, key: str, value: SymbolEntry, permit_overwrite = False):
    if not isinstance(value, SymbolEntry):
      raise Exception(f"not a symbol entry: {value}")
    if self.sanitize:
      key = sanitize(key)
    if not permit_overwrite and key in self.db:
      raise Exception(f"duplicate key '{key}'\n{value}")
    self.db[key] = value
    if not value.address in self.address_db:
      self.address_db[value.address] = []
    self.address_db[value.address].append(value)

  def has(self, key):
    if self.sanitize:
      key = sanitize(key)
    return key in self.db

  def add_entry(self, path, kind, address = 0, external = False, permit_overwrite = False, extra=None) -> bool:
    if self.sanitize:
      path = sanitize(path)
    if path in self.db:
      o = self.get(path)
      if o.kind == kind and o.address == address and o.external == external:
        return False
    self.set(path, SymbolEntry(path, kind, address, external, extra=extra), permit_overwrite=permit_overwrite)
    return True

  def get_all_in_namespace(self, path, recursive = False):
    o = self.get(path)
    if o.kind != 'namespace':
      raise Exception(f"not a namspace: {o}")
    needle = f"{o.path}::"
    c = needle.count("::")
    for p, v in self.db.items():  
      if p.startswith(needle):
        if recursive:
          yield v
        if c == p.count("::"):
          yield v