import unittest
import sqlite3
from database import create_database, get_db_connection

class TestDatabase(unittest.TestCase):

    def setUp(self):
        self.db_path = "test_tarot.db"  # Use a different DB for testing
        create_database(self.db_path)
        self.conn = get_db_connection(self.db_path)
        self.cursor = self.conn.cursor()

    def tearDown(self):
        self.conn.close()
        import os
        os.remove(self.db_path)


    def test_create_database(self):
        # Check if tables exist
        self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = self.cursor.fetchall()
        expected_tables = [('readings',), ('users',), ('spreads',), ('cards',)]  # Add other tables as needed
        self.assertEqual(sorted(tables), sorted(expected_tables))

        # Optionally, check table structure (columns, types, etc.)

    def test_insert_and_retrieve_data(self):
        # Example: Inserting and retrieving a reading
        self.cursor.execute("INSERT INTO readings (spread_id, user_id, reading_date, reading_notes) VALUES (?, ?, ?, ?)", (1, 1, '2024-07-26', 'Test reading'))
        self.conn.commit()

        self.cursor.execute("SELECT * FROM readings WHERE reading_notes = 'Test reading'")
        reading = self.cursor.fetchone()
        self.assertIsNotNone(reading)

    def test_get_db_connection(self):
        conn = get_db_connection(self.db_path)
        self.assertIsInstance(conn, sqlite3.Connection)
        conn.close()


    # Add more test cases for other database interactions (updates, deletes, specific queries)
    def test_invalid_db_path(self):
        with self.assertRaises(sqlite3.OperationalError):
            get_db_connection("invalid/path/to/db.db")