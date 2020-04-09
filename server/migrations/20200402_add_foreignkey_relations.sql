ALTER TABLE responses ADD FOREIGN KEY (username) REFERENCES users(username);
ALTER TABLE drive_details ADD CONSTRAINT uc_sn UNIQUE(serial_number);
ALTER TABLE responses ADD FOREIGN KEY (serial_number) REFERENCES drive_details(serial_number);
ALTER TABLE historical_data ADD FOREIGN KEY (serial_number) REFERENCES drive_details(serial_number);
ALTER TABLE historical_data ADD FOREIGN KEY (username) REFERENCES users(username);
