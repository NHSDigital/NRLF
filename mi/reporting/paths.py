from pathlib import Path

_PATH_TO_HERE = Path(__file__).parent
_PATH_TO_MI_ROOT = _PATH_TO_HERE.parent

PATH_TO_REPORT_SQL = _PATH_TO_MI_ROOT / "sql" / "report.sql"
PATH_TO_REPORT_CSV = _PATH_TO_HERE / "report"
