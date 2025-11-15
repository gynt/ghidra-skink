import re
INSANE = re.compile("[^A-Za-z0-9_-]")
FORBIDDEN_WORDS = ["NULL"]

def sanitize_name(name: str):
  name = re.sub(INSANE, "__", name)
  while name in FORBIDDEN_WORDS:
    name = name + "_"
  return name