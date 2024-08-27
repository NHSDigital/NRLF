import {
  NHS_NUMBERS,
  POINTER_IDS,
  POINTER_TYPES,
  ODS_CODE,
} from "../constants.js";
import http from "k6/http";
import { check, fail } from "k6";

function getHeaders(odsCode = ODS_CODE) {
  return {
    "Content-Type": "application/fhir+json",
    "X-Request-Id": "K6PerformanceTest",
    "NHSD-Correlation-Id": "K6PerformanceTest",
    "NHSD-Connection-Metadata": JSON.stringify({
      "nrl.ods-code": odsCode,
      "nrl.pointer-types": POINTER_TYPES.map(
        (type) => `http://snomed.info/sct|${type}`
      ),
      "nrl.app-id": "K6PerformanceTest",
    }),
    "NHSD-Client-RP-Details": JSON.stringify({
      "developer.app.name": "K6PerformanceTest",
      "developer.app.id": "K6PerformanceTest",
    }),
  };
}

function checkResponse(res) {
  const is_success = check(res, { "status is 200": (r) => r.status === 200 });
  if (!is_success) {
    console.log(res.json());
    fail("Response status is not 200");
  }
}

export function countDocumentReference() {
  const choice = Math.floor(Math.random() * NHS_NUMBERS.length);
  const nhsNumber = NHS_NUMBERS[choice];

  const identifier = encodeURIComponent(
    `https://fhir.nhs.uk/Id/nhs-number|${nhsNumber}`
  );
  const res = http.get(
    `https://${__ENV.HOST}/consumer/DocumentReference/_count?subject:identifier=${identifier}`,
    {
      headers: getHeaders(),
    }
  );
  checkResponse(res);
}

export function readDocumentReference() {
  const choice = Math.floor(Math.random() * POINTER_IDS.length);
  const id = POINTER_IDS[choice];

  const res = http.get(
    `https://${__ENV.HOST}/consumer/DocumentReference/${id}`,
    {
      headers: getHeaders(),
    }
  );

  checkResponse(res);
}

export function searchDocumentReference() {
  const nhsNumber = NHS_NUMBERS[Math.floor(Math.random() * NHS_NUMBERS.length)];
  const pointer_type =
    POINTER_TYPES[Math.floor(Math.random() * POINTER_TYPES.length)];

  const identifier = encodeURIComponent(
    `https://fhir.nhs.uk/Id/nhs-number|${nhsNumber}`
  );
  const type = encodeURIComponent(`http://snomed.info/sct|${pointer_type}`);

  const res = http.get(
    `https://${__ENV.HOST}/consumer/DocumentReference?subject:identifier=${identifier}&type=${type}`,
    {
      headers: getHeaders(),
    }
  );
  checkResponse(res);
}

export function searchPostDocumentReference() {
  const nhsNumber = NHS_NUMBERS[Math.floor(Math.random() * NHS_NUMBERS.length)];
  const pointer_type =
    POINTER_TYPES[Math.floor(Math.random() * POINTER_TYPES.length)];

  const body = JSON.stringify({
    "subject:identifier": `https://fhir.nhs.uk/Id/nhs-number|${nhsNumber}`,
    type: `http://snomed.info/sct|${pointer_type}`,
  });

  const res = http.post(
    `https://${__ENV.HOST}/consumer/DocumentReference/_search`,
    body,
    {
      headers: getHeaders(),
    }
  );
  checkResponse(res);
}
