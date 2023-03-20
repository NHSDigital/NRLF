Feature: Consumer Authorisation Success scenarios

  Background:
    Given template POLICY_RESPONSE
      """
      {
        "principalId": "<transaction-id>",
        "context": {},
        "policyDocument": {
          "Version": "2012-10-17",
          "Statement": [
            {
              "Action": "execute-api:Invoke",
              "Effect": "Allow",
              "Resource": "<resource-arn>"
            }
          ]
        }
      }
      """

  Scenario: Authoriser returns ok for request
    Given Consumer "Yorkshire Ambulance Service" (Organisation ID "RX898") is requesting to read Document Pointers
    And Consumer "Yorkshire Ambulance Service" is registered in the system for application "DataShare" (ID "z00z-y11y-x22x") with pointer types
      | system                 | value           |
      | http://snomed.info/sct | 861421000000109 |
      | http://snomed.info/sct | 861421000000108 |
    When Consumer "Yorkshire Ambulance Service" has their authorisation evaluated
    Then the response is the policy from POLICY_RESPONSE template
