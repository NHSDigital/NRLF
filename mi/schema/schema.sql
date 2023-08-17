CREATE TABLE IF NOT EXISTS dimension.provider (
    provider_id SERIAL PRIMARY KEY,
    provider_name VARCHAR(255),

    UNIQUE (provider_name)
);

CREATE TABLE IF NOT EXISTS dimension.patient (
    patient_id SERIAL PRIMARY KEY,
    patient_hash VARCHAR(255),

    UNIQUE (patient_hash)
);

CREATE TABLE IF NOT EXISTS dimension.document_type (
    document_type_id SERIAL PRIMARY KEY,
    document_type_code VARCHAR(255),
    document_type_system VARCHAR(255),

    UNIQUE (document_type_code, document_type_system)
);

CREATE TABLE IF NOT EXISTS dimension.day (
    day INTEGER PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS dimension.month (
    month INTEGER PRIMARY KEY,
    month_short_name VARCHAR(3),
    month_long_name VARCHAR(9)
);

CREATE TABLE IF NOT EXISTS dimension.year (
    year INTEGER PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS dimension.day_of_week (
    day_of_week INTEGER PRIMARY KEY,
    short_name VARCHAR(3),
    long_name VARCHAR(9)
);

CREATE TABLE IF NOT EXISTS fact.measure (

    --- Dimensions
    provider_id INTEGER,
    patient_id INTEGER,
    document_type_id INTEGER,
    day INTEGER,
    month INTEGER,
    year INTEGER,
    day_of_week INTEGER,

    --- Measures
    count_created INTEGER,
    count_deleted INTEGER,

    partition_key VARCHAR(255) NULL, -- NB: used for isolating test data
    CONSTRAINT PK_measure PRIMARY KEY (year, month, day, patient_id, provider_id, document_type_id),
    FOREIGN KEY (provider_id) REFERENCES dimension.provider (provider_id),
    FOREIGN KEY (patient_id) REFERENCES dimension.patient (patient_id),
    FOREIGN KEY (document_type_id) REFERENCES dimension.document_type (document_type_id),
    FOREIGN KEY (day) REFERENCES dimension.day (day),
    FOREIGN KEY (month) REFERENCES dimension.month (month),
    FOREIGN KEY (year) REFERENCES dimension.year (year),
    FOREIGN KEY (day_of_week) REFERENCES dimension.day_of_week (day_of_week)
);
