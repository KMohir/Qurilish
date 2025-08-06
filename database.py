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
        
        # Удаляем старую таблицу deliveries если она существует
        cursor.execute("DROP TABLE IF EXISTS deliveries CASCADE")
        
        # Таблица пользователей
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                telegram_id BIGINT UNIQUE NOT NULL,
                username VARCHAR(255),
                full_name VARCHAR(255) NOT NULL,
                phone_number VARCHAR(20) NOT NULL,
                role VARCHAR(20) NOT NULL CHECK (role IN ('buyer', 'seller', 'warehouse', 'admin')),
                object_name VARCHAR(255),
                location VARCHAR(500),
                is_approved BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Таблица заявок заказчиков
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS purchase_requests (
                id SERIAL PRIMARY KEY,
                buyer_id INTEGER REFERENCES users(id),
                supplier VARCHAR(255),
                object_name VARCHAR(255),
                request_type VARCHAR(10) CHECK (request_type IN ('excel', 'text')),
                status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'completed', 'cancelled')),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Таблица товаров в заявке
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS request_items (
                id SERIAL PRIMARY KEY,
                request_id INTEGER REFERENCES purchase_requests(id) ON DELETE CASCADE,
                product_name VARCHAR(255),
                quantity DECIMAL(10,2),
                unit VARCHAR(50),
                material_description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Таблица предложений поставщиков
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS seller_offers (
                id SERIAL PRIMARY KEY,
                purchase_request_id INTEGER REFERENCES purchase_requests(id),
                seller_id INTEGER REFERENCES users(id),
                total_amount DECIMAL(10,2),
                offer_type VARCHAR(10) CHECK (offer_type IN ('excel', 'text')),
                status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected', 'delivered')),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Добавляем колонку excel_filename, если она не существует
        try:
            cursor.execute("ALTER TABLE seller_offers ADD COLUMN excel_filename VARCHAR(255)")
            print("✅ Колонка excel_filename добавлена в таблицу seller_offers")
        except Exception as e:
            if "already exists" in str(e) or "duplicate column name" in str(e):
                print("ℹ️ Колонка excel_filename уже существует")
                # Откатываем транзакцию и начинаем новую
                conn.rollback()
                cursor = conn.cursor()
            else:
                print(f"⚠️ Ошибка при добавлении колонки excel_filename: {e}")
                conn.rollback()
                cursor = conn.cursor()
        
        # Таблица деталей предложений (товары с ценами)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS offer_items (
                id SERIAL PRIMARY KEY,
                offer_id INTEGER REFERENCES seller_offers(id) ON DELETE CASCADE,
                product_name VARCHAR(255),
                quantity DECIMAL(15,2),
                unit VARCHAR(50),
                price_per_unit DECIMAL(15,2),
                total_price DECIMAL(15,2),
                material_description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Таблица доставки
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS deliveries (
                id SERIAL PRIMARY KEY,
                offer_id INTEGER REFERENCES seller_offers(id),
                warehouse_user_id INTEGER REFERENCES users(id),
                buyer_id INTEGER REFERENCES users(id),
                status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'delivered', 'received')),
                received_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        cursor.close()
        conn.close()
        print("✅ Таблицы базы данных созданы успешно!")
        
        # Автоматическое исправление типов полей для больших чисел
        self.fix_decimal_fields()
        
        # Автоматическое добавление новых колонок
        self.add_missing_columns()
    
    def fix_decimal_fields(self):
        """Исправление типов полей для поддержки больших чисел"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Список таблиц и полей для исправления
            fixes = [
                ("offer_items", "quantity", "DECIMAL(15,2)"),
                ("offer_items", "price_per_unit", "DECIMAL(15,2)"),
                ("offer_items", "total_price", "DECIMAL(15,2)"),
                ("request_items", "quantity", "DECIMAL(15,2)"),
                ("seller_offers", "total_amount", "DECIMAL(15,2)")
            ]
            
            for table, column, new_type in fixes:
                try:
                    cursor.execute(f"ALTER TABLE {table} ALTER COLUMN {column} TYPE {new_type}")
                    print(f"✅ Исправлен тип поля {table}.{column} на {new_type}")
                except Exception as e:
                    if "already exists" in str(e) or "duplicate column name" in str(e):
                        print(f"ℹ️ Поле {table}.{column} уже имеет правильный тип")
                    else:
                        print(f"⚠️ Ошибка при исправлении {table}.{column}: {e}")
                        
        except Exception as e:
            print(f"⚠️ Ошибка при исправлении типов полей: {e}")
        finally:
            conn.commit()
            cursor.close()
            conn.close()
    
    def add_missing_columns(self):
        """Добавление недостающих колонок в таблицу users"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Добавляем колонку object_name, если она не существует
            try:
                cursor.execute("ALTER TABLE users ADD COLUMN object_name VARCHAR(255)")
                print("✅ Колонка object_name добавлена в таблицу users")
            except Exception as e:
                if "already exists" in str(e) or "duplicate column name" in str(e):
                    print("ℹ️ Колонка object_name уже существует")
                else:
                    print(f"⚠️ Ошибка при добавлении колонки object_name: {e}")
            
            # Добавляем колонку location, если она не существует
            try:
                cursor.execute("ALTER TABLE users ADD COLUMN location VARCHAR(500)")
                print("✅ Колонка location добавлена в таблицу users")
            except Exception as e:
                if "already exists" in str(e) or "duplicate column name" in str(e):
                    print("ℹ️ Колонка location уже существует")
                elif "current transaction is aborted" in str(e):
                    print("ℹ️ Колонка location уже существует (транзакция прервана)")
                else:
                    print(f"⚠️ Ошибка при добавлении колонки location: {e}")
                    
        except Exception as e:
            print(f"⚠️ Ошибка при добавлении колонок: {e}")
        finally:
            conn.commit()
            cursor.close()
            conn.close()
    
    def add_user(self, telegram_id, username, full_name, phone, role, object_name=None, location=None):
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
                username = %s, full_name = %s, phone_number = %s, role = %s, object_name = %s, location = %s
                WHERE telegram_id = %s
            """, (username, full_name, phone, role, object_name, location, telegram_id))
            user_id = existing_user[0]
        else:
            # Добавляем нового пользователя
            is_approved = True if role in ['seller'] else False
            cursor.execute("""
                INSERT INTO users (telegram_id, username, full_name, phone_number, role, object_name, location, is_approved)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING id
            """, (telegram_id, username, full_name, phone, role, object_name, location, is_approved))
            user_id = cursor.fetchone()[0]
        
        conn.commit()
        cursor.close()
        conn.close()
        return user_id
    
    def update_user_object(self, telegram_id, object_name):
        """Обновление объекта пользователя"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE users SET object_name = %s
            WHERE telegram_id = %s
        """, (object_name, telegram_id))
        
        conn.commit()
        cursor.close()
        conn.close()
    
    def update_user_location(self, telegram_id, location):
        """Обновление локации пользователя"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE users SET location = %s
            WHERE telegram_id = %s
        """, (location, telegram_id))
        
        conn.commit()
        cursor.close()
        conn.close()
    
    def get_warehouse_users_by_object(self, object_name):
        """Получение зав. складов по объекту"""
        conn = self.get_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        cursor.execute("""
            SELECT * FROM users 
            WHERE role = 'warehouse' AND object_name = %s AND is_approved = TRUE
        """, (object_name,))
        users = cursor.fetchall()
        
        cursor.close()
        conn.close()
        return users
    
    def get_user(self, telegram_id):
        """Получение пользователя по Telegram ID"""
        conn = self.get_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        cursor.execute("""
            SELECT id, telegram_id, username, full_name, phone_number, role, is_approved, created_at
            FROM users WHERE telegram_id = %s
        """, (telegram_id,))
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
            UPDATE users SET is_approved = TRUE
            WHERE telegram_id = %s
        """, (telegram_id,))
        
        conn.commit()
        cursor.close()
        conn.close()
    
    def add_purchase_request(self, buyer_id, supplier_name, object_name, request_type='excel'):
        """Добавление заявки на покупку"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO purchase_requests (buyer_id, supplier, object_name, request_type)
            VALUES (%s, %s, %s, %s) RETURNING id
        """, (buyer_id, supplier_name, object_name, request_type))
        
        request_id = cursor.fetchone()[0]
        conn.commit()
        cursor.close()
        conn.close()
        return request_id
    
    def add_request_item(self, request_id, product_name, quantity, unit, material_description):
        """Добавление товара в заявку"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO request_items (request_id, product_name, quantity, unit, material_description)
            VALUES (%s, %s, %s, %s, %s) RETURNING id
        """, (request_id, product_name, quantity, unit, material_description))
        
        item_id = cursor.fetchone()[0]
        conn.commit()
        cursor.close()
        conn.close()
        return item_id
    
    def add_seller_offer(self, request_id, seller_id, total_amount, offer_type='excel', excel_filename=None):
        """Добавление предложения поставщика"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO seller_offers (purchase_request_id, seller_id, total_amount, offer_type, excel_filename)
            VALUES (%s, %s, %s, %s, %s) RETURNING id
        """, (request_id, seller_id, total_amount, offer_type, excel_filename))
        
        offer_id = cursor.fetchone()[0]
        conn.commit()
        cursor.close()
        conn.close()
        return offer_id
    
    def add_offer_item(self, offer_id, product_name, quantity, unit, price_per_unit, total_price, material_description):
        """Добавление товара в предложение"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO offer_items (offer_id, product_name, quantity, unit, price_per_unit, total_price, material_description)
            VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id
        """, (offer_id, product_name, quantity, unit, price_per_unit, total_price, material_description))
        
        item_id = cursor.fetchone()[0]
        conn.commit()
        cursor.close()
        conn.close()
        return item_id
    
    def get_pending_requests(self):
        """Получение активных заявок"""
        conn = self.get_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        cursor.execute("""
            SELECT pr.id, pr.buyer_id, 
                   COALESCE(pr.supplier, 'Не указан') as supplier_name, 
                   COALESCE(pr.object_name, 'Не указан') as object_name,
                   pr.status, pr.created_at,
                   u.full_name, u.phone_number
            FROM purchase_requests pr
            JOIN users u ON pr.buyer_id = u.id
            WHERE pr.status = 'active'
            ORDER BY pr.created_at DESC
        """)
        
        requests = cursor.fetchall()
        
        # Получаем товары для каждой заявки
        for request in requests:
            cursor.execute("""
                SELECT * FROM request_items 
                WHERE request_id = %s 
                ORDER BY created_at
            """, (request['id'],))
            request['items'] = cursor.fetchall()
        
        cursor.close()
        conn.close()
        return requests
    
    def get_offers_for_request(self, request_id):
        """Получение предложений для заявки"""
        conn = self.get_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        cursor.execute("""
            SELECT so.*, u.full_name, u.phone_number, so.excel_filename
            FROM seller_offers so
            JOIN users u ON so.seller_id = u.id
            WHERE so.purchase_request_id = %s
            ORDER BY so.created_at DESC
        """, (request_id,))
        
        offers = cursor.fetchall()
        
        # Получаем детали товаров для каждого предложения
        for offer in offers:
            cursor.execute("""
                SELECT * FROM offer_items 
                WHERE offer_id = %s 
                ORDER BY created_at
            """, (offer['id'],))
            offer['items'] = cursor.fetchall()
        
        cursor.close()
        conn.close()
        return offers
    
    def get_approved_offers_for_buyer(self, buyer_id):
        """Получение одобренных предложений для заказчика"""
        conn = self.get_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        cursor.execute("""
            SELECT so.*, u.full_name, u.phone_number, 
                   COALESCE(pr.supplier, 'Не указан') as supplier_name, 
                   COALESCE(pr.object_name, 'Не указан') as object_name
            FROM seller_offers so
            JOIN users u ON so.seller_id = u.id
            JOIN purchase_requests pr ON so.purchase_request_id = pr.id
            WHERE pr.buyer_id = %s AND so.status = 'approved'
            ORDER BY so.created_at DESC
        """, (buyer_id,))
        
        offers = cursor.fetchall()
        
        # Получаем детали товаров для каждого предложения
        for offer in offers:
            cursor.execute("""
                SELECT * FROM offer_items 
                WHERE offer_id = %s 
                ORDER BY created_at
            """, (offer['id'],))
            offer['items'] = cursor.fetchall()
        
        cursor.close()
        conn.close()
        return offers
    
    def update_offer_status(self, offer_id, status):
        """Обновление статуса предложения"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE seller_offers SET status = %s
            WHERE id = %s
        """, (status, offer_id))
        
        conn.commit()
        cursor.close()
        conn.close()
    
    def get_offer_with_items(self, offer_id):
        """Получение предложения с товарами"""
        conn = self.get_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        cursor.execute("""
            SELECT so.*, u.full_name, u.phone_number, u.telegram_id as seller_telegram_id
            FROM seller_offers so
            JOIN users u ON so.seller_id = u.id
            WHERE so.id = %s
        """, (offer_id,))
        
        offer = cursor.fetchone()
        
        if offer:
            cursor.execute("""
                SELECT * FROM offer_items 
                WHERE offer_id = %s 
                ORDER BY created_at
            """, (offer_id,))
            offer['items'] = cursor.fetchall()
        
        cursor.close()
        conn.close()
        return offer
    
    def add_delivery(self, offer_id, warehouse_user_id):
        """Создание записи доставки"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO deliveries (offer_id, warehouse_user_id)
            VALUES (%s, %s) RETURNING id
        """, (offer_id, warehouse_user_id))
        
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
                UPDATE deliveries SET status = %s, received_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (status, delivery_id))
        else:
            cursor.execute("""
                UPDATE deliveries SET status = %s
                WHERE id = %s
            """, (status, delivery_id))
        
        conn.commit()
        cursor.close()
        conn.close()
    
    def get_pending_deliveries(self):
        """Получение ожидающих доставок"""
        conn = self.get_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        cursor.execute("""
            SELECT d.id, d.offer_id, d.warehouse_user_id, d.status, d.received_at, d.created_at,
                   so.total_amount,
                   u_seller.full_name as seller_name,
                   u_seller.phone_number as seller_phone,
                   u_buyer.full_name as buyer_name,
                   u_buyer.phone_number as buyer_phone,
                   pr.supplier, pr.object_name
            FROM deliveries d
            JOIN seller_offers so ON d.offer_id = so.id
            JOIN users u_seller ON so.seller_id = u_seller.id
            JOIN purchase_requests pr ON so.purchase_request_id = pr.id
            JOIN users u_buyer ON pr.buyer_id = u_buyer.id
            WHERE d.status = 'pending'
            ORDER BY d.created_at DESC
        """)
        
        deliveries = cursor.fetchall()
        
        # Получаем товары для каждой доставки
        for delivery in deliveries:
            cursor.execute("""
                SELECT * FROM offer_items 
                WHERE offer_id = %s 
                ORDER BY created_at
            """, (delivery['offer_id'],))
            delivery['items'] = cursor.fetchall()
        
        cursor.close()
        conn.close()
        return deliveries
    
    def get_received_deliveries(self):
        """Получение принятых доставок"""
        conn = self.get_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        cursor.execute("""
            SELECT d.id, d.offer_id, d.warehouse_user_id, d.status, d.received_at, d.created_at,
                   so.total_amount,
                   u_seller.full_name as seller_name,
                   u_seller.phone_number as seller_phone,
                   u_buyer.full_name as buyer_name,
                   u_buyer.phone_number as buyer_phone,
                   pr.supplier, pr.object_name
            FROM deliveries d
            JOIN seller_offers so ON d.offer_id = so.id
            JOIN users u_seller ON so.seller_id = u_seller.id
            JOIN purchase_requests pr ON so.purchase_request_id = pr.id
            JOIN users u_buyer ON pr.buyer_id = u_buyer.id
            WHERE d.status = 'received'
            ORDER BY d.received_at DESC
        """)
        
        deliveries = cursor.fetchall()
        
        # Получаем товары для каждой доставки
        for delivery in deliveries:
            cursor.execute("""
                SELECT * FROM offer_items 
                WHERE offer_id = %s 
                ORDER BY created_at
            """, (delivery['offer_id'],))
            delivery['items'] = cursor.fetchall()
        
        cursor.close()
        conn.close()
        return deliveries 