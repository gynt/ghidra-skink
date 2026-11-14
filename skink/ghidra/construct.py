"""
Fast construction of skink's result dataclasses.
"""

import dataclasses
from typing import Callable, Dict


def fast_constructor(cls):
  """
  Instantiates a skink dataclass without calling its __init__.

  dataclasses_json wraps __init__ of classes with a CatchAll field and resolves
  type hints on every call, which costs ~100us per object. Our arguments are
  already well-typed, so set the fields directly (defaults filled in once).
  """
  defaults = {}
  factories = {}
  for f in dataclasses.fields(cls):
    if f.default is not dataclasses.MISSING:
      defaults[f.name] = f.default
    elif f.default_factory is not dataclasses.MISSING:
      factories[f.name] = f.default_factory
  allocate = object.__new__

  def construct(**kwargs):
    for name, factory in factories.items():
      if name not in kwargs:
        kwargs[name] = factory()
    obj = allocate(cls)
    obj.__dict__ = {**defaults, **kwargs} if defaults else kwargs
    return obj
  return construct


_constructors: Dict[type, Callable] = {}


def new(cls, **kwargs):
  construct = _constructors.get(cls)
  if construct is None:
    construct = _constructors[cls] = fast_constructor(cls)
  return construct(**kwargs)
