CREATE TABLE IF NOT EXISTS dimension.producer (
    producer_id VARCHAR(255) PRIMARY KEY,
    producer_name VARCHAR(255)
);

CREATE TABLE IF NOT EXISTS dimension.consumer (
    consumer_id VARCHAR(255) PRIMARY KEY,
    consumer_name VARCHAR(255)
);

CREATE TABLE IF NOT EXISTS dimension.patient (
    patient_id VARCHAR(255) PRIMARY KEY,
    patient_hash VARCHAR(255)
);

CREATE TABLE IF NOT EXISTS dimension.document_type (
    document_type_id VARCHAR(255) PRIMARY KEY,
    document_type_name VARCHAR(255)
);

CREATE TABLE IF NOT EXISTS dimension.status (
    status_id INTEGER PRIMARY KEY,
    status_name VARCHAR(7)
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

CREATE TABLE IF NOT EXISTS dimension.week (
    week INTEGER PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS dimension.day_of_week (
    day_of_week INTEGER PRIMARY KEY,
    short_name VARCHAR(3),
    long_name VARCHAR(9)
);

CREATE TABLE IF NOT EXISTS fact.measure (
    producer_id VARCHAR(255),
    consumer_id VARCHAR(255),
    patient_id VARCHAR(255),
    document_type_id VARCHAR(255),
    status_id INTEGER,
    day INTEGER,
    month INTEGER,
    year INTEGER,
    week INTEGER,
    day_of_week INTEGER,
    count INTEGER NOT NULL CHECK (count > 0),
    partition_key VARCHAR(255) NULL, -- NB: used for isolating test data
    FOREIGN KEY (status_id) REFERENCES dimension.status (status_id),
    FOREIGN KEY (producer_id) REFERENCES dimension.producer (producer_id),
    FOREIGN KEY (consumer_id) REFERENCES dimension.consumer (consumer_id),
    FOREIGN KEY (patient_id) REFERENCES dimension.patient (patient_id),
    FOREIGN KEY (document_type_id) REFERENCES dimension.document_type (
        document_type_id
    ),
    FOREIGN KEY (day) REFERENCES dimension.day (day),
    FOREIGN KEY (month) REFERENCES dimension.month (month),
    FOREIGN KEY (year) REFERENCES dimension.year (year),
    FOREIGN KEY (week) REFERENCES dimension.week (week),
    FOREIGN KEY (day_of_week) REFERENCES dimension.day_of_week (day_of_week)
);

CREATE INDEX IF NOT EXISTS partition_key_idx ON fact.measure (partition_key);
