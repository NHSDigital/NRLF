export const DEFAULT_TEST_RECORD = open(
  "../data/DocumentReference/Y05868-736253002-Valid.json"
);
export const ODS_CODE = "Y05868";
export const REFERENCE_DATA = JSON.parse(open("./reference-data.json"));
export const POINTER_DOCUMENTS =
  "documents" in REFERENCE_DATA ? REFERENCE_DATA["documents"] : {};
export const ALL_POINTER_IDS =
  "pointer_ids" in REFERENCE_DATA
    ? REFERENCE_DATA["pointer_ids"]
    : Object.keys(POINTER_DOCUMENTS);
export const POINTERS_TO_DELETE = ALL_POINTER_IDS.slice(0, 3500);
export const POINTER_IDS = ALL_POINTER_IDS.slice(3500);
export const NHS_NUMBERS = REFERENCE_DATA["nhs_numbers"];
export const POINTER_TYPES = [
  "736253002",
  "1363501000000100",
  "1382601000000107",
  "325691000000100",
  "736373009",
  "861421000000109",
  "887701000000100",
  "736366004",
  "735324008",
];
