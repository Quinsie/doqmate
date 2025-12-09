import psycopg2
from config import Config

def get_db_connection():
    """DB 접속 객체를 반환하는 함수"""
    conn = psycopg2.connect(**Config.DB_CONFIG)
    return conn