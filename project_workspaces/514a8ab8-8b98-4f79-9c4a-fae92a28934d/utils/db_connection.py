import os
import psycopg2
from urllib.parse import urlparse

from config import DATABASE_URL


def get_db_connection():
    """
    Establishes a connection to the PostgreSQL database based on the provided
    DATABASE_URL environment variable.

    Returns:
        psycopg2.connection: A database connection object.
        None: If the connection fails.
    """
    try:
        if DATABASE_URL:
            url = urlparse(DATABASE_URL)
            dbname = url.path[1:]
            user = url.username
            password = url.password
            host = url.hostname
            port = url.port

            conn = psycopg2.connect(
                dbname=dbname,
                user=user,
                password=password,
                host=host,
                port=port
            )
            return conn
        else:
            return None

    except psycopg2.Error as e:
        print(f"Error connecting to the database: {e}")
        return None


def close_db_connection(conn):
    """
    Closes the provided database connection.

    Args:
        conn (psycopg2.connection): The database connection to close.
    """
    if conn:
        conn.close()