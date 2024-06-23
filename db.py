# db.py
import psycopg2
from psycopg2 import pool

class Database:
    def __init__(self):
        self.conn_pool = psycopg2.pool.SimpleConnectionPool(
            1, 20,
            dbname='films_bot',
            user='projectuser',
            password='password',
            host='localhost'
        )
    
    def get_conn(self):
        return self.conn_pool.getconn()
    
    def put_conn(self, conn):
        self.conn_pool.putconn(conn)
    
    def close_all_conns(self):
        self.conn_pool.closeall()

    def get_user_by_name(self, name):
        conn = self.get_conn()
        try:
            cursor = conn.cursor()
            cursor.execute('SELECT id, name FROM users WHERE name = %s', (name,))
            user = cursor.fetchone()
            return user
        except Exception as error:
            print("Ошибка при работе с PostgreSQL", error)
        finally:
            cursor.close()
            self.put_conn(conn)

db = Database()
