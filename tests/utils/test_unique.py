from dataclasses import dataclass, field

from skink.utils.unique import unique
from skink.export.styles.templates import template_environment


@dataclass
class AP:
  name: str
  location: str
  extra: list = field(default_factory=list)

@dataclass
class Props:
  additionalProperties: AP

@dataclass
class Result:
  properties: Props

@dataclass
class Other:
  properties: Props


def result(name, location="/", extra=None, cls=Result):
  return cls(Props(AP(name, location, extra or [])))


def test_unique_keeps_first_occurrence_in_order():
  a, b, c = result("a"), result("b"), result("c")
  assert unique([a, b, a, c, b]) == [a, b, c]


def test_unique_compares_by_value():
  a1, a2 = result("a"), result("a")
  assert a1 is not a2
  out = unique([a1, a2])
  assert len(out) == 1 and out[0] is a1


def test_unique_same_key_different_value():
  a1, a2 = result("a", extra=[1]), result("a", extra=[2])
  assert unique([a1, a2, a1]) == [a1, a2]


def test_unique_matches_list_membership():
  objs = [result(n, l, e, cls) for n in "ab" for l in ["/", "/x"] for e in [[], [1]] for cls in [Result, Other]]
  objs = objs + [result(n, l, e, cls) for n in "ba" for l in ["/x", "/"] for e in [[1], []] for cls in [Other, Result]]
  expected = []
  for o in objs:
    if o not in expected:
      expected.append(o)
  out = unique(objs)
  assert out == expected
  assert all(x is y for x, y in zip(out, expected))


def test_unique_without_properties():
  assert unique([1, 2, 1, "a", "a", None]) == [1, 2, "a", None]


def test_template_environment_is_shared(tmp_path):
  (tmp_path / "T.j2").write_text("{{ x }}")
  env = template_environment(tmp_path)
  assert template_environment(str(tmp_path)) is env
  assert env.get_template("T.j2") is env.get_template("T.j2")
  assert env.get_template("T.j2").render(x=1) == "1"
