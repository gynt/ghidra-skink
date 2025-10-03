from jinja2 import Environment, FileSystemLoader

env = Environment(loader=FileSystemLoader("skink/export/templates/"))

context = {
    "context": {
      "hash": "3bb0a8c1",
      "abbreviation": "shc",
    },
    "include_paths": [
        "foo/bar.hpp",
        "baz/qux.h",
        "vector",        # system include
        "memory"         # system include
    ],
    "class_name": "A",
    "singleton_name": "DAT_ViewportRenderState",
    "class_size": 320996,
    "namespace_path": "A::B::C",
    "struct_name": "AA",
    "methods": [
      {
        "name": "isValidXY",
        "returnType": "int",
        "parameters": [
          "int x",
          "int y",
        ],
        "parameter_names": ["x", "y"],
        "address": "0x401000",
      },
      {
        "name": "translateXYToTile",
        "returnType": "int",
        "parameters": [
          "int x",
          "int y",
        ],
        "parameter_names": ["x", "y"],
        "address": "0x401000",
      }
    ]
}

template = env.get_template("ClassCPP.j2")

print(template.render(context))