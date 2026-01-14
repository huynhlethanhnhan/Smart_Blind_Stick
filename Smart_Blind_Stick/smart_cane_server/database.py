import mysql.connector
from mysql.connector import Error
from config import Config
import json
from datetime import datetime

class Database:
    def __init__(self):
        self.config = {
            'user': 'username',
            'password': 'password',
            'host': 'localhost',
            'database': 'smart_cane_db',
            'raise_on_warnings': True
        }
        self.connection = None
    
    def connect(self):
        """Connect to MySQL database"""
        try:
            self.connection = mysql.connector.connect(**self.config)
            if self.connection.is_connected():
                print("Connected to MySQL database")
                return True
        except Error as e:
            print(f"Error connecting to MySQL: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from database"""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            print("Database connection closed")
    
    def execute_query(self, query, params=None):
        """Execute SQL query"""
        cursor = None
        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute(query, params or ())
            
            if query.strip().upper().startswith('SELECT'):
                return cursor.fetchall()
            else:
                self.connection.commit()
                return cursor.rowcount
                
        except Error as e:
            print(f"Error executing query: {e}")
            return None
        finally:
            if cursor:
                cursor.close()
    
    def create_tables(self):
        """Create database tables"""
        queries = [
            """
            CREATE TABLE IF NOT EXISTS sensor_data (
                id INT AUTO_INCREMENT PRIMARY KEY,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                front_distance FLOAT,
                left_distance FLOAT,
                right_distance FLOAT,
                ir_distance FLOAT,
                mode INT,
                wifi_strength INT
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS alert_history (
                id INT AUTO_INCREMENT PRIMARY KEY,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                alert_type VARCHAR(50),
                severity VARCHAR(20),
                distance FLOAT,
                location VARCHAR(50),
                resolved BOOLEAN DEFAULT FALSE
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS device_status (
                id INT AUTO_INCREMENT PRIMARY KEY,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                device_id VARCHAR(50) DEFAULT 'ESP32_001',
                power_status BOOLEAN DEFAULT FALSE,
                battery_level INT DEFAULT 100,
                wifi_connected BOOLEAN DEFAULT FALSE,
                last_seen DATETIME
            )
            """,
            """
            CREATE INDEX idx_timestamp ON sensor_data(timestamp);
            """,
            """
            CREATE INDEX idx_alert_timestamp ON alert_history(timestamp);
            """
        ]
        
        for query in queries:
            self.execute_query(query)
        print("Database tables created successfully")
    
    def insert_sensor_data(self, data):
        """Insert sensor data into database"""
        query = """
            INSERT INTO sensor_data 
            (front_distance, left_distance, right_distance, ir_distance, mode, wifi_strength)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        params = (
            data.get('front_distance'),
            data.get('left_distance'),
            data.get('right_distance'),
            data.get('ir_distance'),
            data.get('mode', 1),
            data.get('wifi_strength', -50)
        )
        return self.execute_query(query, params)
    
    def get_recent_data(self, limit=100):
        """Get recent sensor data"""
        query = """
            SELECT * FROM sensor_data 
            ORDER BY timestamp DESC 
            LIMIT %s
        """
        return self.execute_query(query, (limit,))
    
    def get_data_by_time_range(self, start_time, end_time):
        """Get data within time range"""
        query = """
            SELECT * FROM sensor_data 
            WHERE timestamp BETWEEN %s AND %s
            ORDER BY timestamp ASC
        """
        return self.execute_query(query, (start_time, end_time))
    
    def get_statistics(self, hours=24):
        """Get statistics for given time period"""
        query = """
            SELECT 
                AVG(front_distance) as avg_front,
                AVG(left_distance) as avg_left,
                AVG(right_distance) as avg_right,
                AVG(ir_distance) as avg_ir,
                COUNT(*) as total_readings,
                MIN(timestamp) as first_reading,
                MAX(timestamp) as last_reading
            FROM sensor_data 
            WHERE timestamp >= DATE_SUB(NOW(), INTERVAL %s HOUR)
        """
        return self.execute_query(query, (hours,))

# Singleton instance
db_instance = Database()