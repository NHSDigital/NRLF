Feature: Producer Authorisation Failure scenarios

  Background:
    Given template POLICY_RESPONSE
      """
      {
        "principalId": "<transaction-id>",
        "context": {
          "error": "$message"
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
    Given Producer "Aaron Court Mental Health NH" (Organisation ID "8FW23") is requesting to read Document Pointers
    And Producer "Aaron Court Mental Health NH" is registered in the system for application "DataShare" (ID "z00z-y11y-x22x") without any pointer types
    When Producer "Aaron Court Mental Health NH" has their authorisation evaluated
    Then the response is the policy from POLICY_RESPONSE template
      | property | value                               |
      | message  | No pointer types have been provided |

  Scenario: Authoriser rejects request where organisation has not been registered as being associated with the requesting app - using permissions lookup
    Given Producer "Aaron Court Mental Health NH" (Organisation ID "8FW23") is requesting to read Document Pointers
    And Producer "Aaron Court Mental Health NH" is registered in the system for application "DataShare" (ID "z00z-y11y-x22x") without any pointer types stored in NRLF
    When Producer "Aaron Court Mental Health NH" has their authorisation evaluated
    Then the response is the policy from POLICY_RESPONSE template
      | property | value                               |
      | message  | No pointer types have been provided |
