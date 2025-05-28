CREATE DATABASE marketplace_db;
USE marketplace_db;


-- For Shopkeepers
CREATE TABLE shopkeepers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255),
    password VARCHAR(255),
    shop_name VARCHAR(255),
    shop_address TEXT,
    phone_number VARCHAR(15),
    latitude DOUBLE,
    longitude DOUBLE
);

-- For Buyers
CREATE TABLE buyers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255),
    password VARCHAR(255),
    phone_number VARCHAR(15),
    delivery_address TEXT,
    latitude DOUBLE,
    longitude DOUBLE
);
-- For Products
CREATE TABLE products (
    id INT AUTO_INCREMENT PRIMARY KEY,
    shopkeeper_id INT NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    price DECIMAL(10,2) NOT NULL,
    quantity INT NOT NULL,
    image_url VARCHAR(255),
    FOREIGN KEY (shopkeeper_id) REFERENCES shopkeepers(id) ON DELETE CASCADE
);
select * from buyers;
select* from shopkeepers;
;

