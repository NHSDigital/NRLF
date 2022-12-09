Feature: Success scenarios where request is authorised for consumer

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
          "pointer_types": "$pointer-types",
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

  Scenario: Authoriser returns ok for request
    Given Consumer "Yorkshire Ambulance Service" (Organisation ID "RX898") is requesting to read Document Pointers
    And Consumer "Yorkshire Ambulance Service" is registered in the system for application "DataShare" (ID "z00z-y11y-x22x") for document types
      | system                  | value           |
      | https://snomed.info/ict | 861421000000109 |
      | https://snomed.info/ict | 861421000000108 |
    And Consumer "Yorkshire Ambulance Service" has authorisation headers for application "DataShare" (ID "z00z-y11y-x22x")
    When Consumer "Yorkshire Ambulance Service" has their authorisation evaluated
    Then the response is the policy from POLICY_RESPONSE template
      | property          | value                                                                                    |
      | effect            | Allow                                                                                    |
      | application-id    | z00z-y11y-x22x                                                                           |
      | organisation-code | RX898                                                                                    |
      | pointer-types     | ["https://snomed.info/ict\|861421000000109", "https://snomed.info/ict\|861421000000108"] |
