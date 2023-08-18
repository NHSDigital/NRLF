import re
from pathlib import Path

_PATH_TO_HERE = Path(__file__).parent

PATH_TO_QUERIES = _PATH_TO_HERE / "queries"
PATH_TO_REPORT_CSV = _PATH_TO_HERE / "report"
PATH_TO_TEST_DATA = _PATH_TO_HERE / "tests" / "test_data" / "test_data.json"
VALIDATOR_PATH = PATH_TO_QUERIES / "test_validation"

RESOURCE_PREFIX = "nhsd-nrlf"
LAMBDA_NAME = RESOURCE_PREFIX + "--{workspace}--mi--sql_query"
SECRET_NAME = RESOURCE_PREFIX + "--{workspace}--{workspace}--{operation}_password"
DB_CLUSTER_NAME = RESOURCE_PREFIX + "-{env}-aurora-cluster"

SQL_SELECT_REGEX = re.compile(r"SELECT(.*)FROM", flags=re.DOTALL)
SQL_SELECT_SEPARATOR = ","
SQL_ALIAS_SEPARATOR_REGEX = re.compile(
    r"\sas\s|\sAS\s"  # SELECT x AS y (incl. whitespace around AS)
)
SQL_FUNCTION_PARAMS_REGEX = re.compile(r"\(.*,.*\)")

DATE_PATTERN = r"%Y-%m-%d"
