

from typing import List, Tuple

def loc_name_to_location(loc: str, name: str):
  while name[0] == "/":
    name = name[1:]
  while loc[0:1] == "/":
    loc = loc[1:]
  if not loc:
    return "/" + name
  return "/" + loc + "/" + name

# Used
def namespace_to_location(namespace: str):
  while namespace.startswith("::"):
    namespace = namespace[2:]
  return f"/{'/'.join(namespace.split('::'))}"

def location_to_namespace(location: str):
  while location[0] == "/":
    location = location[1:]
  return location.replace("/", "::")

def location_to_loc_name(location: str) -> Tuple[str, str]:
  parts = location.rsplit("/", 1)
  return parts[0], parts[1]

def loc_name_to_parts(loc: str, name: str) -> List[str]:
  return location_to_namespace(loc_name_to_location(loc, name)).split("::")

def loc_name_to_loc_name(loc: str, name: str) -> Tuple[str, str]:
  return location_to_loc_name(loc_name_to_location(loc, name))