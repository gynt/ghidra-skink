from dataclasses import dataclass


@dataclass
class ExportContents:
  path: str
  contents: str
  no_touch: bool = True
  include_preamble: bool = True

  def __repr__(self) -> str:
    if self.no_touch:
      return f"/**\n  AUTO_GENERATED: DO NOT TOUCH THIS FILE\n  path: '{self.path}'\n*/\n\n{self.contents}".replace("\r\n", "\n")
    return f"/**\n  path: '{self.path}'\n*/\n\n{self.contents}".replace("\r\n", "\n")
  
  def serialize(self, no_touch_warning: str = "AUTO_GENERATED: DO NOT TOUCH THIS FILE"):
    if not self.include_preamble:
      return self.contents.replace("\r\n", "\n")
    if self.no_touch:
      return f"/**\n  {no_touch_warning}\n\n  path: '{self.path}'\n*/\n\n{self.contents}".replace("\r\n", "\n")
    return f"/**\n  path: '{self.path}'\n*/\n\n{self.contents}".replace("\r\n", "\n")