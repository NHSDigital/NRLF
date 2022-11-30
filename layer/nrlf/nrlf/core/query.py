from nrlf.core.dynamodb_types import to_dynamodb_dict

ATTRIBUTE_EXISTS_ID = "attribute_exists(id)"


def create_filter_query(**filters) -> dict:
    """
    example:
        create_filter_query(foo="bar", spam=["eggs","hash"])

    will create a DynamoDB client filter, to only include results with:
        * foo must equal "bar"
        * spam must equal one of ("eggs", "hash")

    which in DynamoDB client language is:
        {
            "FilterExpression": "#foo = :foo AND #spam in (:spam0,:spam1)",
            "ExpressionAttributeValues": {":foo": "bar", ":spam0": "eggs", ":spam1": "hash"},
            "ExpressionAttributeNames": {"#foo": "foo", "#spam": "spam"}
        }

    noting that `ExpressionAttributeNames` is required to safeguard against reserved keywords.
    """
    condition_expression = []
    attribute_values = {}
    attribute_names = {}
    for field_name, filter_value in filters.items():
        attribute_names[f"#{field_name}"] = field_name
        if type(filter_value) is list:
            filter_values_alias = ",".join(
                f":{field_name}{idx}" for idx in range(len(filter_value))
            )
            condition_expression.append(f"#{field_name} IN ({filter_values_alias})")
            for idx, value in enumerate(filter_value):
                attribute_values[f":{field_name}{idx}"] = to_dynamodb_dict(value)
        else:
            condition_expression.append(f"#{field_name} = :{field_name}")
            attribute_values[f":{field_name}"] = to_dynamodb_dict(filter_value)
    condition_expression = " AND ".join(condition_expression)

    response = {"ExpressionAttributeValues": attribute_values}

    if attribute_names:
        response["ExpressionAttributeNames"] = attribute_names

    if condition_expression:
        response["FilterExpression"] = condition_expression

    return response


def create_read_and_filter_query(id, **filters):
    read_and_filter_query = create_filter_query(**filters)
    read_and_filter_query["ExpressionAttributeValues"][":id"] = to_dynamodb_dict(id)
    read_and_filter_query["KeyConditionExpression"] = "id = :id"
    return read_and_filter_query


def create_begins_with_read_query(id, **filters):
    read_and_filter_query = create_filter_query(**filters)
    read_and_filter_query["ExpressionAttributeValues"][":id"] = to_dynamodb_dict(id)
    read_and_filter_query["KeyConditionExpression"] = "begins_with(id, :id)"
    return read_and_filter_query


def create_search_and_filter_query(nhs_number, **filters):
    read_and_filter_query = create_filter_query(**filters)
    read_and_filter_query["ExpressionAttributeValues"][
        ":nhs_number"
    ] = to_dynamodb_dict(nhs_number)
    read_and_filter_query["KeyConditionExpression"] = "nhs_number = :nhs_number"
    return read_and_filter_query


def create_hard_delete_query(
    id: str, condition_expression: list = [], **filters
) -> dict:
    attribute_values = {}
    attribute_names = {}

    if len(filters) == 0:
        (condition,) = condition_expression
        return {
            "ConditionExpression": condition,
        }

    for field_name, filter_value in filters.items():
        attribute_names[f"#{field_name}"] = field_name
    if type(filter_value) is list:
        filter_values_alias = ",".join(
            f":{field_name}{idx}" for idx in range(len(filter_value))
        )
        condition_expression.append(f"#{field_name} IN ({filter_values_alias})")
        for idx, value in enumerate(filter_value):
            attribute_values[f":{field_name}{idx}"] = to_dynamodb_dict(value)
    else:
        condition_expression.append(f"#{field_name} = :{field_name}")
        attribute_values[f":{field_name}"] = to_dynamodb_dict(filter_value)

    condition_expression = " AND ".join(condition_expression)

    return {
        "ConditionExpression": condition_expression,
        "ExpressionAttributeNames": attribute_names,
        "ExpressionAttributeValues": attribute_values,
    }


def hard_delete_query(id, **filters):
    hard_delete_query = create_hard_delete_query(
        id=id, condition_expression=[ATTRIBUTE_EXISTS_ID], **filters
    )
    hard_delete_query["Key"] = {"id": to_dynamodb_dict(id)}
    return hard_delete_query


def create_updated_expression_query(**update_values) -> dict:
    """
    example:
        create_updated_expression_query(foo="bar")

    will create a DynamoDB client update, to only include results with:
        * foo must equal "bar"

    which in DynamoDB client language is:
        {
            "UpdateExpression": "SET #foo=:foo,#bar=:bar",
            "ExpressionAttributeValues": {":foo": "123", ":bar": "456"},
            "ExpressionAttributeNames": {"#foo": "foo", "#bar": "bar"}
        }

        ConditionExpression=f"{ATTRIBUTE_EXISTS_ID} AND #producer_id = :producer_id",

    noting that `ExpressionAttributeNames` is required to safeguard against reserved keywords.
    """
    update_expression = []
    attribute_values = {}
    attribute_names = {}

    for field_name, field_value in update_values.items():
        if field_name not in ["created_on", "id"]:
            attribute_names[f"#{field_name}"] = field_name
            update_expression.append(f"#{field_name}=:{field_name}")
            attribute_values[f":{field_name}"] = field_value
    update_expression = ",".join(update_expression)

    return {
        "ConditionExpression": f"{ATTRIBUTE_EXISTS_ID} AND #producer_id = :producer_id",
        "UpdateExpression": "SET {}".format(update_expression),
        "ExpressionAttributeValues": attribute_values,
        "ExpressionAttributeNames": attribute_names,
    }


def update_and_filter_query(**values):
    update_and_filter_query = create_updated_expression_query(**values)
    update_and_filter_query["Key"] = {"id": values["id"]}
    return update_and_filter_query
