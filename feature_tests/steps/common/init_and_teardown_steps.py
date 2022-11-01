from behave import given

from feature_tests.steps.aws.resources.dynamodb import (
    FeatureTestDynamoRepository,
    get_dynamo_db_repository,
)


@given('no "{table_name}" exist in NRLF')
def empty_dynamo_db_table(context, table_name: str):
    repository: FeatureTestDynamoRepository = get_dynamo_db_repository(
        context, table_name
    )
    repository.delete_all()
