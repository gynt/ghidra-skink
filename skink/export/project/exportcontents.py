from dataclasses import dataclass


@dataclass
class ExportContents:
  path: str
  contents: str
  no_touch: bool = True

  def __repr__(self) -> str:
    if self.no_touch:
      return f"/**\n  AUTO_GENERATED: DO NOT TOUCH THIS FILE\n  path: '{self.path}'\n*/\n\n{self.contents}"
    return f"/**\n  path: '{self.path}'\n*/\n\n{self.contents}"