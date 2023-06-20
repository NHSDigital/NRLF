from pathlib import Path

_PATH_TO_HERE = Path(__file__).parent

PATH_TO_QUERIES = _PATH_TO_HERE / "queries"
PATH_TO_REPORT_CSV = _PATH_TO_HERE / "report"
PATH_TO_TEST_DATA = _PATH_TO_HERE / "tests" / "test_data" / "test_data.json"
VALIDATOR_PATH = PATH_TO_QUERIES / "test_validation"
