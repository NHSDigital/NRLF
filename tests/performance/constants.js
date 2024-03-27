export const DEFAULT_TEST_RECORD = open(
  "../data/DocumentReference/Y05868-736253002-Valid.json"
);
export const ODS_CODE = "Y05868";
export const REFERENCE_DATA = JSON.parse(open("./reference-data.json"));
export const POINTER_IDS = REFERENCE_DATA["ids"];
export const NHS_NUMBERS = REFERENCE_DATA["nhs_numbers"];
export const POINTER_TYPES = [
  "http://snomed.info/sct|736253002",
  "http://snomed.info/sct|1363501000000100",
  "http://snomed.info/sct|1382601000000107",
  "http://snomed.info/sct|325691000000100",
  "http://snomed.info/sct|736373009",
  "http://snomed.info/sct|861421000000109",
  "http://snomed.info/sct|887701000000100",
];
