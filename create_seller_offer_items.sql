-- Создание таблицы для товаров в предложениях поставщиков
-- Эта таблица может понадобиться в будущем для более детального хранения товаров

CREATE TABLE seller_offer_items (
    id SERIAL PRIMARY KEY,
    offer_id INTEGER REFERENCES seller_offers(id) ON DELETE CASCADE,
    product_name VARCHAR(255) NOT NULL,
    quantity DECIMAL(10,2) NOT NULL,
    unit VARCHAR(50) NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    total DECIMAL(10,2) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Создание индексов для оптимизации
CREATE INDEX idx_seller_offer_items_offer_id ON seller_offer_items(offer_id);
CREATE INDEX idx_seller_offer_items_product_name ON seller_offer_items(product_name);

-- Комментарий к таблице
COMMENT ON TABLE seller_offer_items IS 'Товары в предложениях поставщиков';
COMMENT ON COLUMN seller_offer_items.offer_id IS 'ID предложения поставщика';
COMMENT ON COLUMN seller_offer_items.product_name IS 'Название товара';
COMMENT ON COLUMN seller_offer_items.quantity IS 'Количество';
COMMENT ON COLUMN seller_offer_items.unit IS 'Единица измерения';
COMMENT ON COLUMN seller_offer_items.price IS 'Цена за единицу';
COMMENT ON COLUMN seller_offer_items.total IS 'Общая сумма';
COMMENT ON COLUMN seller_offer_items.description IS 'Описание товара';
