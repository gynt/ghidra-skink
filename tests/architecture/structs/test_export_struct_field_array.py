


from skink.architecture.common.Field import Field
from skink.export.context import DEFAULT
from skink.architecture.structs.struct import Struct
from skink.sarif.datatypes.StructField import StructField

fieldJSON = """
{
  "offset": 36336,
  "type": {
    "kind": "array",
    "count": 10,
    "subtype": {
      "kind": "array",
      "count": 4,
      "subtype": {
        "kind": "base",
        "size": 4,
        "name": "int",
        "location": "/",
        "settings": [
          {
            "name": "format",
            "kind": "long",
            "value": "1"
          }
        ]
      },
      "name": "int[4]",
      "location": "/",
      "settings": [
        {
          "name": "format",
          "kind": "long",
          "value": "1"
        }
      ]
    },
    "name": "int[10][4]",
    "location": "/",
    "settings": [
      {
        "name": "format",
        "kind": "long",
        "value": "1"
      }
    ]
  },
  "ordinal": 8,
  "length": 160,
  "field_name": "unknownArray01",
  "name": "int[10][4]",
  "location": "/",
  "settings": []
}

"""

def test_export_struct_field_array1():
    sf = StructField.from_json(fieldJSON) # type: ignore
    f = Field(sf)

    assert f.declaration() == "int unknownArray01[10][4];"

    