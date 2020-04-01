
ALTER TABLE responses DROP COLUMN drive_status;

CREATE TABLE IF NOT EXISTS drive_details (
    id SERIAL PRIMARY KEY,
    serial_number text not null,
    username text not null,
    drive_model text not null DEFAULT 'unknown',
    drive_status drive_status_enum DEFAULT 'active',
    drive_nickname text,
    drive_size_bytes bigint DEFAULT 0,
    drive_lba_size_bytes integer DEFAULT 512
);
