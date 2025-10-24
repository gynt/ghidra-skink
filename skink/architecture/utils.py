import re, logging

def extract_array_part(s: str, pattern = re.compile(".*((\\[[0-9]+\\])+)")):
  result = re.match(pattern, s)
  if not result:
    logging.log(logging.WARNING, f"cannot extract array part: '{s}'")
    return ""
  return result.group(1)