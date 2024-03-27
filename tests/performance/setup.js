import { generateNHSNumber } from "./utilities.js";
import {
  ALL_POINTER_TYPES,
  DEFAULT_TEST_RECORD,
  ODS_CODE,
} from "./constants.js";
import { crypto } from "k6/experimental/webcrypto";
import {
  createDocumentReference,
  deleteDocumentReference,
} from "./producer/client.js";
import { fail } from "k6";

const UNIQUE_NHS_NUMBER_COUNT = 5;
const POINTERS_PER_TYPE = 2;

export const CREATED_NHS_NUMBERS = [];
export const CREATED_POINTER_IDS = [];

export function createRecord(nhsNumber, pointerType) {
  const record = JSON.parse(DEFAULT_TEST_RECORD);
  record.id = `${ODS_CODE}-${crypto.randomUUID()}`;

  record.type.coding[0].code = pointerType;
  record.type.coding[0].display = ALL_POINTER_TYPES[pointerType];
  record.subject.identifier.value = nhsNumber;
  record.context.sourcePatientInfo.identifier.value = nhsNumber;

  return record;
}

export function createTestRecords() {
  for (let i = 0; i < UNIQUE_NHS_NUMBER_COUNT; i++) {
    const nhsNumber = generateNHSNumber();
    CREATED_NHS_NUMBERS.push(nhsNumber);

    for (const pointerType of Object.keys(ALL_POINTER_TYPES)) {
      for (let j = 0; j < POINTERS_PER_TYPE; j++) {
        const record = createRecord(nhsNumber, pointerType);
        CREATED_POINTER_IDS.push(record.id);
        const result = createDocumentReference(JSON.stringify(record));

        if (result.status !== 201) {
          console.error(`Failed to create record`);
          fail(`Failed to create record: ${result.status}`);
        }
      }
    }
  }
}

export function deleteTestRecords() {
  for (const pointerId of CREATED_POINTER_IDS) {
    console.log(pointerId);
    deleteDocumentReference(pointerId);
  }
}
