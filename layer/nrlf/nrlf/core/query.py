from nrlf.core.dynamodb_types import to_dynamodb_dict


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

    return {
        "FilterExpression": condition_expression,
        "ExpressionAttributeValues": attribute_values,
        "ExpressionAttributeNames": attribute_names,
    }


def create_read_and_filter_query(id, **filters):
    read_and_filter_query = create_filter_query(**filters)
    read_and_filter_query["ExpressionAttributeValues"][":id"] = to_dynamodb_dict(id)
    read_and_filter_query["KeyConditionExpression"] = "id = :id"
    return read_and_filter_query


def create_search_and_filter_query(nhs_number, **filters):
    read_and_filter_query = create_filter_query(**filters)
    read_and_filter_query["ExpressionAttributeValues"][
        ":nhs_number"
    ] = to_dynamodb_dict(nhs_number)
    read_and_filter_query["KeyConditionExpression"] = "nhs_number = :nhs_number"
    return read_and_filter_query
