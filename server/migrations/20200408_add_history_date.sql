ALTER TABLE historical_data ADD created_at TIMESTAMP DEFAULT NOW();
ALTER TABLE historical_data DROP drive_status;