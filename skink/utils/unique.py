from typing import Any, Dict, Hashable, Iterable, List, TypeVar

T = TypeVar("T")

def _key(obj: Any) -> Hashable:
  # Equal results have equal keys, so only objects with the same key need comparing
  ap = getattr(getattr(obj, "properties", None), "additionalProperties", None)
  key = (type(obj), getattr(ap, "name", None), getattr(ap, "location", None))
  try:
    hash(key)
  except TypeError:
    return type(obj)
  return key

def unique(objects: Iterable[T]) -> List[T]:
  """
  Returns objects without duplicates (by ==), in order of first occurrence.

  Same result as appending each object not yet `in` the list, without comparing every pair.
  """
  result: List[T] = []
  buckets: Dict[Hashable, List[T]] = {}
  for obj in objects:
    bucket = buckets.setdefault(_key(obj), [])
    if obj not in bucket:
      bucket.append(obj)
      result.append(obj)
  return result
