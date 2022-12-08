Feature: Success scenarios where request is authorised for producer

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
          "document_types": "$document-types",
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
    Given Producer "Aaron Court Mental Health NH" (Organisation ID "8FW23") is requesting to read Document Pointers
    And Producer "Aaron Court Mental Health NH" is registered in the system for application "DataShare" (ID "z00z-y11y-x22x") for document types
      | system                  | value           |
      | https://snomed.info/ict | 861421000000109 |
      | https://snomed.info/ict | 861421000000108 |
    And Producer "Aaron Court Mental Health NH" has authorisation headers for application "DataShare" (ID "z00z-y11y-x22x")
    When Producer "Aaron Court Mental Health NH" has their authorisation evaluated
    Then the response is the policy from POLICY_RESPONSE template
      | property          | value                                                                                    |
      | effect            | Allow                                                                                    |
      | application-id    | z00z-y11y-x22x                                                                           |
      | organisation-code | 8FW23                                                                                    |
      | document-types    | ["https://snomed.info/ict\|861421000000109", "https://snomed.info/ict\|861421000000108"] |
