def authorisation_ok(principal_id, resource, context):
    return _create_policy(principal_id, resource, "Allow", context)


def authorisation_denied(principal_id, resource, context):
    return _create_policy(principal_id, resource, "Deny", context)


def _create_policy(principal_id, resource, effect, context):
    return {
        "principalId": principal_id,
        "context": context,
        "policyDocument": {
            "Version": "2012-10-17",
            "Statement": [
                {"Action": "execute-api:Invoke", "Effect": effect, "Resource": resource}
            ],
        },
    }
