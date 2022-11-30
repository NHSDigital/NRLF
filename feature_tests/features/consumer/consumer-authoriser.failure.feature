Feature: Failure scenarios where request is authorised for consumer

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

  Scenario: Authoriser rejects request where organisation is not associated with supplied application
    Given a request for "Yorkshire Ambulance Service" contains all the correct headers to be authorised
    And the following organisation to application relationship exists
      | organisation                | application |
      | Yorkshire Ambulance Service | SCRa        |
    And "Yorkshire Ambulance Service" can access the following document types
      | system                  | value           |
      | https://snomed.info/ict | 861421000000109 |
      | https://snomed.info/ict | 861421000000108 |
    When Consumer "Yorkshire Ambulance Service" makes a request
      | property           | value            |
      | developer.app.id   | application_two  |
      | developer.app.name | application name |
    Then returns the correct deny policy to consumer
      | property     | value     |
      | principal_id | nhsd-corr |
      | effect       | Deny      |
      | resource     | methodarn |

  Scenario: Authoriser rejects request where the organisation has no stored document types
    Given a request for "organisation_two" contains all the correct headers to be authorised
    And the following organisation to application relationship exists
      | organisation                | application |
      | Yorkshire Ambulance Service | SCRa        |
    And "Yorkshire Ambulance Service" can access the following document types
      | system                  | value           |
      | https://snomed.info/ict | 861421000000109 |
      | https://snomed.info/ict | 861421000000108 |
    When Consumer "Yorkshire Ambulance Service" makes a request
      | property           | value            |
      | developer.app.id   | SCRa             |
      | developer.app.name | application name |
    Then returns the correct deny policy to consumer
      | property     | value     |
      | principal_id | nhsd-corr |
      | effect       | Deny      |
      | resource     | methodarn |
