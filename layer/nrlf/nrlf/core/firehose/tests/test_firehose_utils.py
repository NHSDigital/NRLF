import base64

from nrlf.core.firehose.utils import (
    dump_json_gzip,
    encode_log_events_as_ndjson,
    list_in_chunks,
    load_json_gzip,
    name_from_arn,
)


def test_encode_log_events():
    assert (
        encode_log_events_as_ndjson(["foo", "bar"])
        == base64.b64encode(b'"foo"\n"bar"').decode()
    )


def test_name_from_arn():
    name = name_from_arn(
        "arn:partition:service:region:account-id:resource-type/resource-id"
    )  # https://docs.aws.amazon.com/general/latest/gr/aws-arns-and-namespaces.html
    assert name == "resource-id"


def test_serialisation():
    original = ["foo"]
    dumped = dump_json_gzip(obj=original)
    loaded = load_json_gzip(data=dumped)
    assert loaded == original


def test_list_in_chunks():
    chunks = list(list_in_chunks(items=["a", "b", "c", "d", "e"], batch_size=2))
    assert chunks == [["a", "b"], ["c", "d"], ["e"]]
