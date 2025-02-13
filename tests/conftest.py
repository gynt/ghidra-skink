import shutil
from typing import List
import pytest
import json

from skink.sarif import SarifExport
from skink.sarif.BasicResult import BasicResult

@pytest.fixture
def example_collect_joint_data() -> List[BasicResult]:
    with open("tests/data/example1.sarif.json", 'r') as f:
      j = json.load(f)
      sarifExport1: SarifExport = SarifExport.from_dict(j)   
    return sarifExport1.runs[0].results

@pytest.fixture
def example_class_example_functions_fixture():
    with open("tests/data/class-example.sarif.json", 'r') as f:
      j = json.load(f)
      sarifExport: SarifExport = SarifExport.from_dict(j)
      vprs_functions = [f for f in sarifExport.runs[0].results if f.ruleId == "FUNCTIONS"]
      return vprs_functions

@pytest.fixture
def example_struct_example_fixture():
    with open("tests/data/struct-example.sarif.json", 'r') as f:
      j = json.load(f)
      sarifExport: SarifExport = SarifExport.from_dict(j)
      dts = [f for f in sarifExport.runs[0].results if f.ruleId == "DATATYPE"]
      return dts

def pytest_assertrepr_compare(config, op, left, right):
    # https://docs.pytest.org/en/latest/reference/reference.html#pytest.hookspec.pytest_assertrepr_compare
    if isinstance(left, str) and isinstance(right, str) and op == "==":
        left_lines = left.splitlines(keepends=True)
        left_lines = [l.replace("\t", "\\t") for l in left_lines]
        left_lines = [l.replace(" ", "\\s") for l in left_lines]
        left_lines = [l.replace("\r", "\\r") for l in left_lines]
        right_lines = right.splitlines(keepends=True)
        right_lines = [l.replace("\t", "\\t") for l in right_lines]
        right_lines = [l.replace(" ", "\\s") for l in right_lines]
        right_lines = [l.replace("\r", "\\r") for l in right_lines]
        if len(left_lines) > 1 or len(right_lines) > 1:
            width, _ = shutil.get_terminal_size(fallback=(80, 24))
            width = max(width, 40) - 10
            lines = [
                "When comparing multiline strings:",
                f" LEFT ({len(left)}) ".center(width, "="),
                *left_lines,
                f" RIGHT ({len(right)}) ".center(width, "="),
                *right_lines,
            ]
            return lines