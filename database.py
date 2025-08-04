import psycopg2
import psycopg2.extras
from datetime import datetime
from config import DB_CONFIG

class Database:
    def __init__(self):
        self.config = DB_CONFIG
    
    def get_connection(self):
        """Получение соединения с базой данных"""
        return psycopg2.connect(**self.config)
    
    async def create_user(self, telegram_id, username, full_name, phone_number, role):
        """Создание нового пользователя"""
        conn = self.get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO users (telegram_id, username, full_name, phone_number, role)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (telegram_id) DO UPDATE SET
                    username = EXCLUDED.username,
                    full_name = EXCLUDED.full_name,
                    phone_number = EXCLUDED.phone_number,
                    role = EXCLUDED.role
                    RETURNING id
                """, (telegram_id, username, full_name, phone_number, role))
                user_id = cursor.fetchone()[0]
                conn.commit()
                return user_id
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    async def get_user(self, telegram_id):
        """Получение пользователя по telegram_id"""
        conn = self.get_connection()
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT * FROM users WHERE telegram_id = %s
                """, (telegram_id,))
                return cursor.fetchone()
        finally:
            conn.close()
    
    async def approve_user(self, telegram_id):
        """Одобрение пользователя администратором"""
        conn = self.get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    UPDATE users SET is_approved = TRUE WHERE telegram_id = %s
                """, (telegram_id,))
                conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    async def get_sellers(self):
        """Получение всех продавцов"""
        conn = self.get_connection()
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT * FROM users WHERE role = 'seller' AND is_approved = TRUE
                """)
                return cursor.fetchall()
        finally:
            conn.close()
    
    async def create_purchase_request(self, buyer_id, supplier, object_name, product_name, 
                                   quantity, unit, material_description, request_type):
        """Создание заявки на покупку"""
        conn = self.get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO purchase_requests 
                    (buyer_id, supplier, object_name, product_name, quantity, unit, material_description, request_type)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (buyer_id, supplier, object_name, product_name, quantity, unit, material_description, request_type))
                request_id = cursor.fetchone()[0]
                conn.commit()
                return request_id
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    async def create_seller_offer(self, purchase_request_id, seller_id, price, total_amount, offer_type):
        """Создание предложения продавца"""
        conn = self.get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO seller_offers 
                    (purchase_request_id, seller_id, price, total_amount, offer_type)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id
                """, (purchase_request_id, seller_id, price, total_amount, offer_type))
                offer_id = cursor.fetchone()[0]
                conn.commit()
                return offer_id
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    async def get_purchase_requests_for_buyer(self, buyer_id):
        """Получение заявок покупателя"""
        conn = self.get_connection()
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT * FROM purchase_requests WHERE buyer_id = %s ORDER BY created_at DESC
                """, (buyer_id,))
                return cursor.fetchall()
        finally:
            conn.close()
    
    async def get_offers_for_request(self, purchase_request_id):
        """Получение предложений для заявки"""
        conn = self.get_connection()
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT so.*, u.full_name, u.phone_number 
                    FROM seller_offers so
                    JOIN users u ON so.seller_id = u.id
                    WHERE so.purchase_request_id = %s
                    ORDER BY so.created_at DESC
                """, (purchase_request_id,))
                return cursor.fetchall()
        finally:
            conn.close()
    
    async def get_seller_offers(self, seller_id):
        """Получение предложений продавца"""
        conn = self.get_connection()
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT * FROM seller_offers WHERE seller_id = %s ORDER BY created_at DESC
                """, (seller_id,))
                return cursor.fetchall()
        finally:
            conn.close()
    
    async def approve_offer(self, offer_id):
        """Одобрение предложения продавца"""
        conn = self.get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    UPDATE seller_offers SET status = 'approved' WHERE id = %s
                """, (offer_id,))
                conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    async def create_delivery(self, offer_id, warehouse_user_id):
        """Создание записи о доставке"""
        conn = self.get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO deliveries (offer_id, warehouse_user_id)
                    VALUES (%s, %s)
                    RETURNING id
                """, (offer_id, warehouse_user_id))
                delivery_id = cursor.fetchone()[0]
                conn.commit()
                return delivery_id
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    async def mark_delivery_received(self, delivery_id):
        """Отметка получения товара на складе"""
        conn = self.get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    UPDATE deliveries 
                    SET delivery_status = 'received', received_at = %s
                    WHERE id = %s
                """, (datetime.now(), delivery_id))
                conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    async def get_pending_deliveries(self):
        """Получение ожидающих доставок"""
        conn = self.get_connection()
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT d.*, so.*, u.full_name as seller_name, u.phone_number as seller_phone
                    FROM deliveries d
                    JOIN seller_offers so ON d.offer_id = so.id
                    JOIN users u ON so.seller_id = u.id
                    WHERE d.delivery_status = 'pending'
                    ORDER BY d.created_at DESC
                """)
                return cursor.fetchall()
        finally:
            conn.close()
    
    async def get_delivery_info(self, delivery_id):
        """Получение информации о доставке"""
        conn = self.get_connection()
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT d.*, so.*, pr.buyer_id, u.telegram_id as buyer_telegram_id
                    FROM deliveries d
                    JOIN seller_offers so ON d.offer_id = so.id
                    JOIN purchase_requests pr ON so.purchase_request_id = pr.id
                    JOIN users u ON pr.buyer_id = u.id
                    WHERE d.id = %s
                """, (delivery_id,))
                return cursor.fetchone()
        finally:
            conn.close()
    
    async def get_pending_users(self):
        """Получение пользователей ожидающих одобрения"""
        conn = self.get_connection()
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT * FROM users WHERE is_approved = FALSE AND role != 'seller'
                    ORDER BY created_at DESC
                """)
                return cursor.fetchall()
        finally:
            conn.close()
    
    async def reject_offer(self, offer_id):
        """Отклонение предложения продавца"""
        conn = self.get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    UPDATE seller_offers SET status = 'rejected' WHERE id = %s
                """, (offer_id,))
                conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    async def get_offer_info(self, offer_id):
        """Получение информации о предложении"""
        conn = self.get_connection()
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT so.*, u.telegram_id as seller_telegram_id
                    FROM seller_offers so
                    JOIN users u ON so.seller_id = u.id
                    WHERE so.id = %s
                """, (offer_id,))
                return cursor.fetchone()
        finally:
            conn.close() 