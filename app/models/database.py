import mysql.connector
from app.config import Config


def get_connection(database=None):
    return mysql.connector.connect(
        host=Config.MYSQL_HOST,
        port=Config.MYSQL_PORT,
        user=Config.MYSQL_USER,
        password=Config.MYSQL_PASSWORD,
        database=database or Config.VAULTSYNC_DB
    )