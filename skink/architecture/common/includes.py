from skink.architecture.common.exclusion import filter_includes
from skink.export.context import Context
from skink.export.types import generate_include_for_type_location


def includes_for_type_name_location(type_name: str, type_location: str, ctx: Context):
  yield from filter_includes(generate_include_for_type_location(type_name, type_location, ctx), ctx)