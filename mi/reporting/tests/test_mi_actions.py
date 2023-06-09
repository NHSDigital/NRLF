from pathlib import Path
from tempfile import TemporaryDirectory

from mi.reporting.actions import make_query_event, perform_query, write_csv


def test_make_query_event():
    query_event = make_query_event()
    assert query_event.dict() == {}


def test_perform_query(mock_session, mock_lambda):
    data_dict = perform_query(session=mock_session, function_name=mock_lambda, event={})
    assert data_dict == [{}]


def test_write_csv():
    with TemporaryDirectory() as path:
        out_path = write_csv(data_dict=[{}], path=path, env="foo")
        assert out_path == f"{path}/something"
        assert Path(out_path).exists()
