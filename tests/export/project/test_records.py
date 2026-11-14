import json

from skink.export.project.project import Project
from skink.export.project.databaseplan import DatatypeDatabasePlan, DefineddataDatabasePlan, FunctionDatabasePlan, SymbolsDatabasePlan


def raw_objects():
  with open("tests/data/example1.sarif.json", 'r') as f:
    results = json.load(f)["runs"][0]["results"]
  # Results skink does not build its database from: not decoded, and skipped
  return [{"ruleId": "COMMENTS"}, {"ruleId": "DATATYPE", "message": {"text": "DT.Base"}}] + results


def build(project: Project) -> Project:
  project.build_database(plan_symbols=SymbolsDatabasePlan(store_symbol_result=True),
                         plan_datatype=DatatypeDatabasePlan(),
                         plan_defineddata=DefineddataDatabasePlan(),
                         plan_function=FunctionDatabasePlan())
  return project


def test_yield_records_decodes_database_results():
  records = list(Project(raw_objects=raw_objects()).yield_records())
  assert sorted((ruleId, subtype, type(obj).__name__) for ruleId, subtype, obj in records) == [
    ("DATATYPE", "DT.Struct", "DataTypeResult"),
    ("FUNCTIONS", "Function", "FunctionResult"),
    ("FUNCTIONS", "Function", "FunctionResult"),
  ]
  assert [r[0] for r in Project(raw_objects=raw_objects()).yield_records(["FUNCTIONS"])] == ["FUNCTIONS", "FUNCTIONS"]


def test_records_build_the_same_database():
  sarif = build(Project(raw_objects=raw_objects()))
  records = list(Project(raw_objects=raw_objects()).yield_records())
  # A record source may also yield types skink has no class for, e.g. DT.Base
  base = ("DATATYPE", "DT.Base", records[0][2])
  from_records = build(Project(records=[base] + records))
  assert sarif.db_datatype and sarif.db_function
  assert from_records.db_datatype == sarif.db_datatype
  assert from_records.db_function == sarif.db_function
  assert from_records.db_defineddata == sarif.db_defineddata
  assert from_records.db_meta == sarif.db_meta
  assert list(from_records.yield_objects()) == [base[2]] + [obj for _, _, obj in records]


def test_project_without_cache_path():
  assert Project(path="tests/data/example1.sarif.json").cache_path is None
