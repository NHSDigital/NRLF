import http from "k6/http";
import {
  POINTER_TYPES,
  ODS_CODE,
  NHS_NUMBERS,
  POINTER_IDS,
  POINTER_DOCUMENTS,
  POINTERS_TO_DELETE,
} from "../constants.js";
import { check, fail } from "k6";
import { randomItem } from "https://jslib.k6.io/k6-utils/1.2.0/index.js";
import { crypto } from "k6/experimental/webcrypto";
import { createRecord } from "../setup.js";

function getBaseURL() {
  return `https://${__ENV.HOST}/producer/DocumentReference`;
}

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
    console.warn(res.json());
    fail("Response status is not 200");
  }
}

export function createDocumentReference() {
  const nhsNumber = randomItem(NHS_NUMBERS);
  const pointerType = randomItem(POINTER_TYPES);
  const record = createRecord(nhsNumber, pointerType);

  const res = http.post(getBaseURL(), JSON.stringify(record), {
    headers: getHeaders(),
  });

  check(res, { "create status is 201": (r) => r.status === 201 });

  if (res.status !== 201) {
    console.warn(
      `Failed to create record: ${res.status}: ${
        JSON.parse(res.body).issue[0].diagnostics
      }`
    );
    fail("Response status was not 201");
  }
}

export function readDocumentReference() {
  const id = randomItem(POINTER_IDS);

  const res = http.get(`${getBaseURL()}/${id}`, { headers: getHeaders() });

  checkResponse(res);
}

export function updateDocumentReference() {
  const id = randomItem(POINTER_IDS);
  const document = POINTER_DOCUMENTS[id];

  document.content[0].attachment.url = "https://example.com/k6-updated-url.pdf";

  const res = http.put(`${getBaseURL()}/${id}`, JSON.stringify(document), {
    headers: getHeaders(),
  });

  checkResponse(res);
}

export function deleteDocumentReference() {
  const id = randomItem(POINTERS_TO_DELETE);

  const res = http.del(`${getBaseURL()}/${id}`, null, {
    headers: getHeaders(),
  });

  checkResponse(res);
}

export function upsertDocumentReference() {
  const nhsNumber = randomItem(NHS_NUMBERS);
  const pointerType = randomItem(POINTER_TYPES);
  const record = createRecord(nhsNumber, pointerType);

  record.id = `k6perf-${crypto.randomUUID()}`;

  const res = http.post(getBaseURL(), JSON.stringify(record), {
    headers: getHeaders(),
  });

  check(res, { "create status is 201": (r) => r.status === 201 });

  if (res.status !== 201) {
    console.warn(
      `Failed to create record: ${res.status}: ${
        JSON.parse(res.body).issue[0].diagnostics
      }`
    );
    fail("Response status was not 201");
  }
}

export function searchDocumentReference() {
  const nhsNumber = randomItem(NHS_NUMBERS);
  const pointerType = randomItem(POINTER_TYPES);

  const identifier = encodeURIComponent(
    `https://fhir.nhs.uk/Id/nhs-number|${nhsNumber}`
  );
  const type = encodeURIComponent(`http://snomed.info/sct|${pointerType}`);

  const url = `${getBaseURL()}?subject:identifier=${identifier}&type=${type}`;

  const res = http.get(url, {
    headers: getHeaders(),
  });

  check(res, { "status is 200": (r) => r.status === 200 });

  if (res.status !== 200) {
    console.log(
      `Search failed with ${res.status}: ${JSON.stringify(res.body)}`
    );
    fail("Response status was not 200");
  }
}

export function searchPostDocumentReference() {
  const nhsNumber = randomItem(NHS_NUMBERS);
  const pointerType = randomItem(POINTER_TYPES);

  const body = JSON.stringify({
    "subject:identifier": `https://fhir.nhs.uk/Id/nhs-number|${nhsNumber}`,
    type: `http://snomed.info/sct|${pointerType}`,
  });

  const res = http.post(`${getBaseURL()}/_search`, body, {
    headers: getHeaders(),
  });

  check(res, { "status is 200": (r) => r.status === 200 });

  if (res.status !== 200) {
    console.log(
      `Search failed with ${res.status}: ${JSON.stringify(res.body)}`
    );
    fail("Response status was not 200");
  }
}
