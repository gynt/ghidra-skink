import re
INSANE = re.compile("[^A-Za-z0-9_]")
FORBIDDEN_WORDS = ["NULL", "char", "int", "short", "long", "void", "unsigned", "delete"]

def sanitize_name(name: str):
  name = re.sub(INSANE, "__", name)
  while name in FORBIDDEN_WORDS:
    name = name + "_"
  return name

CALLING_CONVENTIONS = ["__thiscall", "__cdecl", "__stdcall", "__fastcall"]

def sanitize_calling_convention(cc: str):
  for CC in CALLING_CONVENTIONS:
    if cc == CC:
      return cc
    if cc.startswith(CC):
      return CC
  raise Exception(f"unknown calling convention: {cc}")