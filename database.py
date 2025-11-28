"""
Database management for VerificationAPI
"""

import pymysql
import os
from datetime import datetime
from typing import Optional, Dict, Any
from urllib.parse import urlparse

# Get MySQL connection details from Railway environment variable
def get_db_config():
    """Parse DATABASE_URL or use Railway's individual MySQL variables"""
    # Try Railway's individual variables first (MYSQLHOST, MYSQLUSER, etc.)
    mysql_host = os.environ.get('MYSQLHOST')
    
    if mysql_host:
        # Use Railway's individual environment variables
        return {
            'host': mysql_host,
            'port': int(os.environ.get('MYSQLPORT', 3306)),
            'user': os.environ.get('MYSQLUSER', 'root'),
            'password': os.environ.get('MYSQLPASSWORD', ''),
            'database': os.environ.get('MYSQLDATABASE', 'railway'),
            'charset': 'utf8mb4',
            'cursorclass': pymysql.cursors.DictCursor
        }
    
    # Try parsing DATABASE_URL or MYSQL_URL
    database_url = os.environ.get('DATABASE_URL') or os.environ.get('MYSQL_URL')
    
    if database_url and not database_url.startswith('${{'):
        # Parse connection string (only if not a template)
        url = urlparse(database_url)
        return {
            'host': url.hostname,
            'port': url.port or 3306,
            'user': url.username,
            'password': url.password,
            'database': url.path[1:],  # Remove leading '/'
            'charset': 'utf8mb4',
            'cursorclass': pymysql.cursors.DictCursor
        }
    
    # Fallback for local development
    return {
        'host': os.environ.get('MYSQL_HOST', 'localhost'),
        'port': int(os.environ.get('MYSQL_PORT', 3306)),
        'user': os.environ.get('MYSQL_USER', 'root'),
        'password': os.environ.get('MYSQL_PASSWORD', ''),
        'database': os.environ.get('MYSQL_DATABASE', 'verification_db'),
        'charset': 'utf8mb4',
        'cursorclass': pymysql.cursors.DictCursor
    }


def init_database():
    """Initialize the MySQL database with the verification table"""
    try:
        conn = pymysql.connect(**get_db_config())
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS verifications (
                id INT AUTO_INCREMENT PRIMARY KEY,
                robloxUsername VARCHAR(255) UNIQUE NOT NULL,
                robloxID VARCHAR(255) NOT NULL,
                discordUsername VARCHAR(255) NOT NULL,
                discordID VARCHAR(255) NOT NULL,
                timeToVerify VARCHAR(255) NOT NULL,
                joinedGame TINYINT(1) DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_robloxUsername (robloxUsername)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        ''')
        
        conn.commit()
        conn.close()
        print("Database initialized successfully")
    except Exception as e:
        print(f"Error initializing database: {e}")
        raise


def get_connection():
    """Get a MySQL database connection"""
    return pymysql.connect(**get_db_config())


def add_verification(roblox_username: str, roblox_id: str, discord_username: str, 
                     discord_id: str, time_to_verify: str, joined_game: bool = False) -> bool:
    """Add a new verification entry"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO verifications (robloxUsername, robloxID, discordUsername, discordID, timeToVerify, joinedGame)
            VALUES (%s, %s, %s, %s, %s, %s)
        ''', (roblox_username, roblox_id, discord_username, discord_id, time_to_verify, int(joined_game)))
        
        conn.commit()
        conn.close()
        return True
    except pymysql.IntegrityError:
        # Username already exists, update instead
        return update_verification(roblox_username, roblox_id, discord_username, discord_id, time_to_verify, joined_game)
    except Exception as e:
        print(f"Error adding verification: {e}")
        return False


def update_verification(roblox_username: str, roblox_id: str, discord_username: str, 
                        discord_id: str, time_to_verify: str, joined_game: bool = False) -> bool:
    """Update an existing verification entry"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE verifications 
            SET robloxID = %s, discordUsername = %s, discordID = %s, timeToVerify = %s, joinedGame = %s
            WHERE robloxUsername = %s
        ''', (roblox_id, discord_username, discord_id, time_to_verify, int(joined_game), roblox_username))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error updating verification: {e}")
        return False


def get_verification_by_username(roblox_username: str) -> Optional[Dict[str, Any]]:
    """Get verification data by Roblox username"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT robloxUsername, robloxID, discordUsername, discordID, timeToVerify, joinedGame
        FROM verifications
        WHERE robloxUsername = %s
    ''', (roblox_username,))
    
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return {
            'robloxUsername': row['robloxUsername'],
            'robloxID': row['robloxID'],
            'discordUsername': row['discordUsername'],
            'discordID': row['discordID'],
            'timeToVerify': row['timeToVerify'],
            'joinedGame': bool(row['joinedGame'])
        }
    return None


def update_joined_game(roblox_username: str, joined_game: bool) -> bool:
    """Update only the joinedGame field for a user"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE verifications 
            SET joinedGame = %s
            WHERE robloxUsername = %s
        ''', (int(joined_game), roblox_username))
        
        updated = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return updated
    except Exception as e:
        print(f"Error updating joinedGame: {e}")
        return False


def delete_verification_by_username(roblox_username: str) -> bool:
    """Delete verification data by Roblox username"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM verifications WHERE robloxUsername = %s', (roblox_username,))
        
        deleted = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return deleted
    except Exception as e:
        print(f"Error deleting verification: {e}")
        return False


def check_and_delete_expired(time_to_verify: str) -> bool:
    """Check if timeToVerify has expired and return True if expired"""
    try:
        # Parse the timeToVerify timestamp
        # Assuming format: ISO 8601 or Unix timestamp
        try:
            # Try parsing as Unix timestamp (seconds)
            expiry_time = datetime.fromtimestamp(float(time_to_verify))
        except (ValueError, TypeError):
            # Try parsing as ISO 8601
            expiry_time = datetime.fromisoformat(time_to_verify.replace('Z', '+00:00'))
        
        # Check if expired
        return datetime.now() > expiry_time
    except Exception as e:
        print(f"Error checking expiration: {e}")
        return False
