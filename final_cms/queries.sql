CREATE DATABASE flask_db;

USE flask_db;

CREATE TABLE admin (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL
);

INSERT INTO admin (name, email, password) VALUES ('Municipal Commissioner', 'mc@gmail.com', '$2b$12$ZEmF6LmEwV9h3LGOWk4zQu3FBNhgwJ9q4V51/9dXev29xD4PNCK5W');

CREATE TABLE complaints (
	id INT AUTO_INCREMENT PRIMARY KEY,
    kobo_id BIGINT UNIQUE,
	name VARCHAR(100),
    phone_number VARCHAR(20),
    mail_id VARCHAR(100),
	date DATE,
    type_of_hazard ENUM('pot_hole', 'electric_line'),
    geolocation_latitude DECIMAL(9,6),
    geolocation_longitude DECIMAL(9,6),
	status ENUM('Unresolved', 'Resolved', 'In Progress') DEFAULT 'Unresolved',
    escalated ENUM('Yes', 'No') DEFAULT 'No'
);

