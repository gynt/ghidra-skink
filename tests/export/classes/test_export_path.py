from skink.export.classes.collect import collect_classes
from skink.export.context import DEFAULT

def test_export_path1(example_collect_joint_data):
    results = example_collect_joint_data

    classes = collect_classes(results)

    ctx = DEFAULT
    ctx.class_rules = ctx.class_rules.mutate(inline_struct = True)

    cls = next(classes)
    assert cls.structure is not None
    assert cls.path() == "A/B/BClass.h"