import re
NUMERIC = re.compile("[0-9]+")
INSANE = re.compile("[^A-Za-z0-9_]")
FORBIDDEN_WORDS = ["NULL", "char", "int", "short", "long", "void", "unsigned", "delete"]

def sanitize_name(name: str):
  if re.match(NUMERIC, name[0]):
    name = "_" + name
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
  if cc == "unknown":
    return "__cdecl"
  raise Exception(f"unknown calling convention: {cc}")