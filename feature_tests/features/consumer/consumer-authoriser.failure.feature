Feature: Consumer Authorisation Failure scenarios

  Background:
    Given template POLICY_RESPONSE
      """
      {
        "principalId": "<transaction-id>",
        "context": {
          "error": "{\"message\": \"$message\"}"
        },
        "policyDocument": {
          "Version": "2012-10-17",
          "Statement": [
            {
              "Action": "execute-api:Invoke",
              "Effect": "Deny",
              "Resource": "<resource-arn>"
            }
          ]
        }
      }
      """

  Scenario: Authoriser rejects request where organisation has not been registered as being associated with the requesting app
    Given Consumer "Yorkshire Ambulance Service" (Organisation ID "RX898") is requesting to read Document Pointers
    And Consumer "Yorkshire Ambulance Service" is registered in the system for application "DataShare" (ID "z00z-y11y-x22x") without any pointer types
    When Consumer "Yorkshire Ambulance Service" has their authorisation evaluated
    Then the response is the policy from POLICY_RESPONSE template
      | property | value                               |
      | message  | No pointer types have been provided |
