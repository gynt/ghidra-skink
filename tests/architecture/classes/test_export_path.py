from skink.architecture.classes.cls import Class
from skink.architecture.classes.collect import collect_classes
from skink.architecture.functions.function import Function
from skink.export.context import DEFAULT
from skink.sarif.datatypes.DataTypeResult import DataTypeResult

def test_export_path1(example_collect_joint_data):
    results = example_collect_joint_data

    classes = collect_classes(results)

    ctx = DEFAULT
    ctx.class_rules = ctx.class_rules.mutate(inline_struct = True)

    cls = next(classes)
    assert cls.structure is not None
    assert cls.path() == "A/B/BClass.h"