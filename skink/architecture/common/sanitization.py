import re
INSANE = re.compile("[^A-Za-z0-9_-]")

def sanitize_name(name: str):
  return re.sub(INSANE, "__", name)