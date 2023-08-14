SELECT
    dimension.provider.provider_name AS provider_name,
    dimension.patient.patient_hash AS patient,
    dimension.document_type.document_type_code AS document_type_code,
    dimension.document_type.document_type_system AS document_type_system,
    dimension.day.day AS day,
    dimension.month.month_short_name AS month,
    dimension.year.year AS year,
    fact.measure.count_created AS count_created,
    fact.measure.count_deleted AS count_deleted
FROM fact.measure
INNER JOIN dimension.provider ON fact.measure.provider_id = dimension.provider.provider_id
INNER JOIN dimension.patient ON fact.measure.patient_id = dimension.patient.patient_id
INNER JOIN dimension.document_type ON fact.measure.document_type_id = dimension.document_type.document_type_id
INNER JOIN dimension.day ON fact.measure.day = dimension.day.day
INNER JOIN dimension.month ON fact.measure.month = dimension.month.month
INNER JOIN dimension.year ON fact.measure.year = dimension.year.year
