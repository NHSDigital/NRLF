import http from "k6/http";
import { ALL_POINTER_TYPES, ODS_CODE } from "../constants.js";
import { check } from "k6";

function getBaseURL() {
  return `https://${__ENV.HOST}/producer/DocumentReference`;
}

function getHeaders(odsCode = ODS_CODE, pointerTypes = ALL_POINTER_TYPES) {
  return {
    "Content-Type": "application/fhir+json",
    "NHSD-Connection-Metadata": JSON.stringify({
      "nrl.ods-code": odsCode,
      "nrl.pointer-types": Object.keys(pointerTypes).map(
        (pointerType) => `http://snomed.info/sct|${pointerType}`
      ),
    }),
    "NHSD-Client-RP-Details": JSON.stringify({
      "developer.app.name": "K6PerformanceTest",
      "developer.app.id": "K6PerformanceTest",
    }),
  };
}

export function createDocumentReference(document) {
  return http.post(getBaseURL(), document, { headers: getHeaders() });
}

export function deleteDocumentReference(document_id) {
  const url = `${getBaseURL()}/${document_id}`;
  return http.del(url, { headers: getHeaders() });
}
