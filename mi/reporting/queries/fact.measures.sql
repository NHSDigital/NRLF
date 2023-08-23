SELECT
    provider_id,
    patient_id,
    document_type_id,
    day,
    month,
    year,
    day_of_week,
    count_created,
    count_deleted
FROM fact.measure
WHERE partition_key = %(partition_key)s
LIMIT 1000;
