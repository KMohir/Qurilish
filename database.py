import psycopg2
import psycopg2.extras
from datetime import datetime
import pytz
from config import DB_CONFIG, TIMEZONE

class Database:
    def __init__(self):
        self.config = DB_CONFIG
        self.timezone = pytz.timezone(TIMEZONE)
    
    def get_connection(self):
        return psycopg2.connect(**self.config)
    
    def create_tables(self):
        """Создание всех необходимых таблиц"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Таблица пользователей
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                telegram_id BIGINT UNIQUE NOT NULL,
                username VARCHAR(255),
                first_name VARCHAR(255),
                last_name VARCHAR(255),
                phone VARCHAR(20),
                role VARCHAR(50) NOT NULL,
                is_approved BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Таблица заявок покупателей
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS purchase_requests (
                id SERIAL PRIMARY KEY,
                buyer_id INTEGER REFERENCES users(id),
                supplier_name VARCHAR(255),
                object_name VARCHAR(255),
                product_name VARCHAR(255),
                quantity DECIMAL,
                unit VARCHAR(50),
                material_description TEXT,
                status VARCHAR(50) DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Таблица предложений продавцов
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS seller_offers (
                id SERIAL PRIMARY KEY,
                request_id INTEGER REFERENCES purchase_requests(id),
                seller_id INTEGER REFERENCES users(id),
                price DECIMAL,
                total_amount DECIMAL,
                status VARCHAR(50) DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Таблица доставки
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS deliveries (
                id SERIAL PRIMARY KEY,
                offer_id INTEGER REFERENCES seller_offers(id),
                warehouse_user_id INTEGER REFERENCES users(id),
                buyer_id INTEGER REFERENCES users(id),
                status VARCHAR(50) DEFAULT 'pending',
                received_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        cursor.close()
        conn.close()
        print("✅ Таблицы базы данных созданы успешно!")
    
    def add_user(self, telegram_id, username, first_name, last_name, phone, role):
        """Добавление нового пользователя"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Проверяем, существует ли пользователь
        cursor.execute("SELECT id, role FROM users WHERE telegram_id = %s", (telegram_id,))
        existing_user = cursor.fetchone()
        
        if existing_user:
            # Обновляем существующего пользователя
            cursor.execute("""
                UPDATE users SET 
                username = %s, first_name = %s, last_name = %s, 
                phone = %s, role = %s, updated_at = CURRENT_TIMESTAMP
                WHERE telegram_id = %s
            """, (username, first_name, last_name, phone, role, telegram_id))
            user_id = existing_user[0]
        else:
            # Добавляем нового пользователя
            is_approved = True if role in ['seller'] else False
            cursor.execute("""
                INSERT INTO users (telegram_id, username, first_name, last_name, phone, role, is_approved)
                VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id
            """, (telegram_id, username, first_name, last_name, phone, role, is_approved))
            user_id = cursor.fetchone()[0]
        
        conn.commit()
        cursor.close()
        conn.close()
        return user_id
    
    def get_user(self, telegram_id):
        """Получение пользователя по Telegram ID"""
        conn = self.get_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        cursor.execute("SELECT * FROM users WHERE telegram_id = %s", (telegram_id,))
        user = cursor.fetchone()
        
        cursor.close()
        conn.close()
        return user
    
    def get_users_by_role(self, role):
        """Получение всех пользователей по роли"""
        conn = self.get_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        cursor.execute("SELECT * FROM users WHERE role = %s AND is_approved = TRUE", (role,))
        users = cursor.fetchall()
        
        cursor.close()
        conn.close()
        return users
    
    def approve_user(self, telegram_id):
        """Одобрение пользователя администратором"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE users SET is_approved = TRUE, updated_at = CURRENT_TIMESTAMP
            WHERE telegram_id = %s
        """, (telegram_id,))
        
        conn.commit()
        cursor.close()
        conn.close()
    
    def add_purchase_request(self, buyer_id, supplier_name, object_name, product_name, quantity, unit, material_description):
        """Добавление заявки на покупку"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO purchase_requests (buyer_id, supplier_name, object_name, product_name, quantity, unit, material_description)
            VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id
        """, (buyer_id, supplier_name, object_name, product_name, quantity, unit, material_description))
        
        request_id = cursor.fetchone()[0]
        conn.commit()
        cursor.close()
        conn.close()
        return request_id
    
    def add_seller_offer(self, request_id, seller_id, price, total_amount):
        """Добавление предложения продавца"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO seller_offers (request_id, seller_id, price, total_amount)
            VALUES (%s, %s, %s, %s) RETURNING id
        """, (request_id, seller_id, price, total_amount))
        
        offer_id = cursor.fetchone()[0]
        conn.commit()
        cursor.close()
        conn.close()
        return offer_id
    
    def get_pending_requests(self):
        """Получение активных заявок"""
        conn = self.get_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        cursor.execute("""
            SELECT pr.*, u.first_name, u.last_name, u.phone
            FROM purchase_requests pr
            JOIN users u ON pr.buyer_id = u.id
            WHERE pr.status = 'active'
            ORDER BY pr.created_at DESC
        """)
        
        requests = cursor.fetchall()
        cursor.close()
        conn.close()
        return requests
    
    def get_offers_for_request(self, request_id):
        """Получение предложений для заявки"""
        conn = self.get_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        cursor.execute("""
            SELECT so.*, u.first_name, u.last_name, u.phone
            FROM seller_offers so
            JOIN users u ON so.seller_id = u.id
            WHERE so.request_id = %s
            ORDER BY so.created_at DESC
        """, (request_id,))
        
        offers = cursor.fetchall()
        cursor.close()
        conn.close()
        return offers
    
    def update_offer_status(self, offer_id, status):
        """Обновление статуса предложения"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE seller_offers SET status = %s, updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """, (status, offer_id))
        
        conn.commit()
        cursor.close()
        conn.close()
    
    def add_delivery(self, offer_id, warehouse_user_id, buyer_id):
        """Создание записи доставки"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO deliveries (offer_id, warehouse_user_id, buyer_id)
            VALUES (%s, %s, %s) RETURNING id
        """, (offer_id, warehouse_user_id, buyer_id))
        
        delivery_id = cursor.fetchone()[0]
        conn.commit()
        cursor.close()
        conn.close()
        return delivery_id
    
    def update_delivery_status(self, delivery_id, status):
        """Обновление статуса доставки"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if status == 'received':
            cursor.execute("""
                UPDATE deliveries SET status = %s, received_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (status, delivery_id))
        else:
            cursor.execute("""
                UPDATE deliveries SET status = %s, updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (status, delivery_id))
        
        conn.commit()
        cursor.close()
        conn.close() 