Feature: Failure scenarios where request is authorised for consumer

  Background:
    Given template POLICY_RESPONSE
      """
      {
        "principalId": "<nhsd-correlation-id>",
        "context": {
          "x-correlation-id": "<x-correlation-id>",
          "nhsd-correlation-id": "<nhsd-correlation-id>",
          "request-type": "app_restricted",
          "developer.app.name": "<developer.app.name>",
          "developer.app.id": "$application-id",
          "Organisation-Code": "$organisation-code"
        },
        "policyDocument": {
          "Version": "2012-10-17",
          "Statement": [
            {
              "Action": "execute-api:Invoke",
              "Effect": "$effect",
              "Resource": "<resource-arn>"
            }
          ]
        }
      }
      """
    And template NULL_POLICY_RESPONSE
      """
      {
        "principalId": "null",
        "context": {},
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
    And Consumer "Yorkshire Ambulance Service" has authorisation headers for application "DataShare" (ID "z00z-y11y-x22x")
    And Consumer "Yorkshire Ambulance Service" is not registered in the system for application "DataShare" (ID "z00z-y11y-x22x")
    When Consumer "Yorkshire Ambulance Service" has their authorisation evaluated
    Then the response is the policy from POLICY_RESPONSE template
      | property          | value          |
      | effect            | Deny           |
      | application-id    | z00z-y11y-x22x |
      | organisation-code | RX898          |

  Scenario: Authoriser rejects request with authorisation headers for an application for which it does not have permissions
    Given Consumer "Yorkshire Ambulance Service" (Organisation ID "RX898") is requesting to read Document Pointers
    And Consumer "Yorkshire Ambulance Service" is registered in the system for application "DataShare" (ID "z00z-y11y-x22x") for document types
      | system                  | value           |
      | https://snomed.info/ict | 861421000000109 |
      | https://snomed.info/ict | 861421000000108 |
    And Consumer "Yorkshire Ambulance Service" has authorisation headers for application "AnotherAppId456" (ID "a33a-b22b-c11c")
    When Consumer "Yorkshire Ambulance Service" has their authorisation evaluated
    Then the response is the policy from POLICY_RESPONSE template
      | property          | value          |
      | effect            | Deny           |
      | application-id    | a33a-b22b-c11c |
      | organisation-code | RX898          |

  Scenario: Authoriser rejects request without authorisation headers for the requesting app
    Given Consumer "Yorkshire Ambulance Service" (Organisation ID "RX898") is requesting to read Document Pointers
    And Consumer "Yorkshire Ambulance Service" does not have authorisation headers for application "DataShare" (ID "z00z-y11y-x22x")
    And Consumer "Yorkshire Ambulance Service" is registered in the system for application "DataShare" (ID "z00z-y11y-x22x") for document types
      | system                  | value           |
      | https://snomed.info/ict | 861421000000109 |
      | https://snomed.info/ict | 861421000000108 |
    When Consumer "Yorkshire Ambulance Service" has their authorisation evaluated
    Then the response is the policy from NULL_POLICY_RESPONSE template
