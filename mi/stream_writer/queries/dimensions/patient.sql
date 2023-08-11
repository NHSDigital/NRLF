INSERT INTO dimension.patient
(
    patient_hash
)
VALUES (
   %(patient_hash)s
)
ON CONFLICT (patient_hash) DO NOTHING
