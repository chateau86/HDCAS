CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- User table

CREATE TABLE IF NOT EXISTS users (
    username TEXT PRIMARY KEY NOT NULL,
    email TEXT,
    password_hash TEXT NOT NULL DEFAULT 'invalid',
    current_token uuid UNIQUE NOT NULL DEFAULT gen_random_uuid() 
);

DROP TYPE IF EXISTS drive_status_enum;
CREATE TYPE drive_status_enum as enum ('active', 'retired', 'failed');

CREATE TABLE IF NOT EXISTS responses (
    id SERIAL PRIMARY KEY,
    serial_number text not null,
    username text not null,
    raw_smart_json text,
    response_json text,
    drive_status drive_status_enum DEFAULT 'active',
    created_at TIMESTAMP DEFAULT NOW()
);
