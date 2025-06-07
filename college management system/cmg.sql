CREATE DATABASE IF NOT EXISTS college_db;
USE college_db;

CREATE TABLE colleges (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) UNIQUE
);

CREATE TABLE students (
    id INT AUTO_INCREMENT PRIMARY KEY,
    roll INT,
    name VARCHAR(100),
    age INT,
    email VARCHAR(100),
    branch VARCHAR(100),
    college_name VARCHAR(100),
    FOREIGN KEY (college_name) REFERENCES colleges(name)
);

CREATE TABLE teachers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100),
    age INT,
    email VARCHAR(100),
    department VARCHAR(50),
    college_name VARCHAR(100)
);
ALTER TABLE teachers ADD subject VARCHAR(100);
SELECT DISTINCT college_name FROM students;


select * from students