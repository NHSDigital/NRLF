# from dataclasses import asdict

# from hypothesis import given
# from hypothesis.strategies import builds, just, sampled_from

# from mi.stream_writer.constants import TYPE_SEPARATOR
# from mi.stream_writer.model import DIMENSION_TYPES, Dimension, RecordParams
# from nrlf.core.model import DocumentPointer

NHS_NUMBER = "123"
CREATED_ON = "2000-01-01T01:02:03.1232Z"
SYSTEM = "abc"
VALUE = "def"


# document_pointer_strategy = {
#     k: print(v.annotation.__annotations__)
#     for k, v in DocumentPointer.model_fields.items()
# }

#     # k: builds(v.type_.__fields__["__root__"].type_)
#     # for k, v in DocumentPointer.__fields__.items()


# @given(
#     **{
#         **document_pointer_strategy,
#         **{
#             "nhs_number": just(NHS_NUMBER),
#             "type": just(TYPE_SEPARATOR.join((SYSTEM, VALUE))),
#             "created_on": just(CREATED_ON),
#         },
#     }
# )
# def test_record_from_document_pointer(**document_pointer):
#     record = RecordParams.from_document_pointer(**document_pointer)
#     provider_name = document_pointer["custodian"]
#     if document_pointer["custodian_suffix"]:
#         provider_name += f"{document_pointer['custodian_suffix']}"
#     assert record == RecordParams(
#         provider_name=provider_name,
#         patient_hash="a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3",  # pragma: allowlist secret
#         document_type_system=SYSTEM,
#         document_type_code=VALUE,
#         created_date="2000-01-01 01:02:03",
#         created_date_weekday=5,
#     )


# @given(record=builds(RecordParams), dimension_type=sampled_from(DIMENSION_TYPES))
# def test_record_to_dimension(record: RecordParams, dimension_type: Dimension):
#     dimension = record.to_dimension(dimension_type=dimension_type)
#     _dimension = asdict(dimension)
#     _record = asdict(record)
#     assert all(k in _record for k in _dimension)
#     assert all(_record[k] == v for k, v in _dimension.items())
