Feature: Producer Authorisation Success scenarios

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
    Given Producer "Aaron Court Mental Health NH" (Organisation ID "8FW23") is requesting to read Document Pointers
    And Producer "Aaron Court Mental Health NH" is registered in the system for application "DataShare" (ID "z00z-y11y-x22x") with pointer types
      | system                  | value           |
      | https://snomed.info/ict | 861421000000109 |
      | https://snomed.info/ict | 861421000000108 |
    When Producer "Aaron Court Mental Health NH" has their authorisation evaluated
    Then the response is the policy from POLICY_RESPONSE template
