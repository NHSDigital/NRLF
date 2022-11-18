Feature: Success scenarios where request is authorised for consumer

  Background:
    Given example HEADERS
      """
      {
        "x-correlation-id": "x-corr",
        "nhsd-correlation-id": "nhsd-corr",
        "request-type": "app_restricted",
        "Accept": "version=1",
        "Authorization": "letmein",
        "x-request-id": "requestid"
      }
      """
    Given template POLICY_RESPONSE
      """
      {
        "principalId": "$principal_id",
        "context": "$context",
        "policyDocument": {
          "Version": "2012-10-17",
          "Statement": [
            {
              "Action": "execute-api:Invoke",
              "Effect": "$effect",
              "Resource": "$resource"
            }
          ]
        }
      }
      """

  Scenario: Authoriser returns ok for request
    Given a request contains all the correct headers to be authorised
    When Consumer "AARON COURT MENTAL NH" makes a request
      | property           | value            |
      | developer.app.id   | application id   |
      | developer.app.name | application name |
    Then returns the correct policy
      | property     | value     |
      | principal_id | nhsd-corr |
      | effect       | Allow     |
      | resource     | methodarn |
