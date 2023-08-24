INSERT INTO fact.measure
(
    provider_id,
    patient_id,
    document_type_id,
    year,
    month,
    day,
    day_of_week,
    count_created,
    count_deleted
)
VALUES (
    (SELECT provider_id FROM dimension.provider WHERE provider_name = %(provider_name)s),
    (SELECT patient_id FROM dimension.patient WHERE patient_hash = %(patient_hash)s),
    (SELECT document_type_id FROM dimension.document_type WHERE document_type_system = %(document_type_system)s AND document_type_code = %(document_type_code)s),
    EXTRACT(YEAR FROM TIMESTAMP %(created_date)s),
    EXTRACT(MONTH FROM TIMESTAMP %(created_date)s),
    EXTRACT(DAY FROM TIMESTAMP %(created_date)s),
    %(created_date_weekday)s,
    1,
    0
)
ON CONFLICT (year, month, day, patient_id, provider_id, document_type_id) DO UPDATE
SET count_created = fact.measure.count_created + 1;
