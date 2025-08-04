-- Создание базы данных для системы закупок
CREATE DATABASE sfx_savdo_db;

-- Подключение к базе данных
\c sfx_savdo_db;

-- Таблица пользователей
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    telegram_id BIGINT UNIQUE NOT NULL,
    username VARCHAR(255),
    full_name VARCHAR(255) NOT NULL,
    phone_number VARCHAR(20) NOT NULL,
    role VARCHAR(20) NOT NULL CHECK (role IN ('buyer', 'seller', 'warehouse', 'admin')),
    is_approved BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица заявок на покупку
CREATE TABLE purchase_requests (
    id SERIAL PRIMARY KEY,
    buyer_id INTEGER REFERENCES users(id),
    supplier VARCHAR(255),
    object_name VARCHAR(255),
    product_name VARCHAR(255),
    quantity DECIMAL(10,2),
    unit VARCHAR(50),
    material_description TEXT,
    request_type VARCHAR(10) CHECK (request_type IN ('excel', 'text')),
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'completed', 'cancelled')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица предложений продавцов
CREATE TABLE seller_offers (
    id SERIAL PRIMARY KEY,
    purchase_request_id INTEGER REFERENCES purchase_requests(id),
    seller_id INTEGER REFERENCES users(id),
    price DECIMAL(10,2),
    total_amount DECIMAL(10,2),
    offer_type VARCHAR(10) CHECK (offer_type IN ('excel', 'text')),
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected', 'delivered')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица доставок
CREATE TABLE deliveries (
    id SERIAL PRIMARY KEY,
    offer_id INTEGER REFERENCES seller_offers(id),
    warehouse_user_id INTEGER REFERENCES users(id),
    delivery_status VARCHAR(20) DEFAULT 'pending' CHECK (delivery_status IN ('pending', 'received', 'completed')),
    received_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Создание индексов для оптимизации
CREATE INDEX idx_users_telegram_id ON users(telegram_id);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_purchase_requests_buyer_id ON purchase_requests(buyer_id);
CREATE INDEX idx_seller_offers_request_id ON seller_offers(purchase_request_id);
CREATE INDEX idx_seller_offers_seller_id ON seller_offers(seller_id);
CREATE INDEX idx_deliveries_offer_id ON deliveries(offer_id);

-- Вставка администратора (замените на реальные данные)
INSERT INTO users (telegram_id, username, full_name, phone_number, role, is_approved) 
VALUES (123456789, 'admin', 'Администратор', '+998901234567', 'admin', TRUE); 