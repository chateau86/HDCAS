ALTER TABLE historical_data ADD created_at TIMESTAMP DEFAULT NOW();
ALTER TABLE historical_data DROP drive_status;
ALTER TABLE responses ADD CONSTRAINT UQ_response UNIQUE(serial_number, username);