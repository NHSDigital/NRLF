import { POINTER_TYPES, DEFAULT_TEST_RECORD, ODS_CODE } from "./constants.js";
import { crypto } from "k6/experimental/webcrypto";

export function createRecord(nhsNumber, pointerType) {
  const record = JSON.parse(DEFAULT_TEST_RECORD);
  record.id = `${ODS_CODE}-${crypto.randomUUID()}`;

  record.type.coding[0].code = pointerType;
  record.type.coding[0].display = POINTER_TYPES[pointerType];
  record.subject.identifier.value = nhsNumber;
  record.context.sourcePatientInfo.identifier.value = nhsNumber;

  return record;
}
