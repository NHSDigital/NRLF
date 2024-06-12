DEFAULT_TEST_SUBJECT = """
"subject": {
  "identifier": {
    "system": "https://fhir.nhs.uk/Id/nhs-number",
    "value": "9999999999"
  }
}
"""

DEFAULT_TEST_AUTHOR = """
"author": [{
  "identifier": {
    "system": "https://fhir.nhs.uk/Id/ods-organization-code",
    "value": "TSTAUT"
  }
}]
"""

DEFAULT_TEST_CUSTODIAN = """
"custodian": {
  "identifier": {
    "system": "https://fhir.nhs.uk/Id/ods-organization-code",
    "value": "TSTCUS"
  }
}
"""

DEFAULT_TEST_TYPE = """
"type": {
  "coding": [
    {
      "system": "http://snomed.info/sct",
      "code": "1363501000000100",
      "display": "Royal College of Physicians NEWS2 (National Early Warning Score 2) chart"
    }
  ]
}
"""

DEFAULT_TEST_CATEGORY = """
"category": [
  {
    "coding": [
      {
        "system": "http://snomed.info/sct",
        "code": "1102421000000108",
        "display": "Observations"
      }
    ]
  }
]
"""

DEFAULT_TEST_MASTER_ID = """
"masterIdentifier": {
  "system": "test-master-id-default-system",
  "value": "test-master-id-default-value"
}
"""

DEFAULT_TEST_CONTEXT = """
"context": {
  "related": [
    {
      "identifier": {
        "system": "https://fhir.nhs.uk/Id/nhsSpineASID",
        "value": "230811201350"
      }
    }
  ]
}
"""

DEFAULT_TEST_DESCRIPTION = """
"description": "This is the default description for a test pointer."
"""

DEFAULT_TEST_SECURITY_LABEL = """
"securityLabel": [
  {
    "coding": [
      {
        "system": "http://terminology.hl7.org/CodeSystem/v3-Confidentiality",
        "code": "V",
        "display": "very restricted"
      }
    ]
  }
]
"""

DEFAULT_TEST_CONTENT = """
"content": [
  {
    "attachment": {
        "contentType": "application/pdf",
        "language": "en-UK",
        "url": "https://spine-proxy.national.ncrs.nhs.uk/https%3A%2F%2Fp1.nhs.uk%2FMentalhealthCrisisPlanReport.pdf",
        "hash": "2jmj7l5rSw0yVb/vlWAYkK/YBwk=",
        "title": "Mental health crisis plan report",
        "creation": "2022-12-21T10:45:41+11:00"
    },
    "format": {
        "system": "https://fhir.nhs.uk/England/CodeSystem/England-NRLFormatCode",
        "code": "urn:nhs-ic:unstructured",
        "display": "Unstructured document"
    }
  }
]
"""
