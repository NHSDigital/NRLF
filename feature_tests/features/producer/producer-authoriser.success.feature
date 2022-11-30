Feature: Success scenarios where request is authorised for producer

  Background:
    Given example HEADERS
      """
      {
          "request-type": "app_restricted",
          "Accept": "version=1",
          "Authorization": "letmein"
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
    Given a request for "Yorkshire Ambulance Service" contains all the correct headers to be authorised
    When Producer "Yorkshire Ambulance Service" makes a request
      | property           | value            |
      | developer.app.id   | application id   |
      | developer.app.name | application name |
    Then returns the correct allow policy
      | property     | value     |
      | principal_id | nhsd-corr |
      | effect       | Allow     |
      | resource     | methodarn |
