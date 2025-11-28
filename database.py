"""
Database management for VerificationAPI
"""

import sqlite3
import os
from datetime import datetime
from typing import Optional, Dict, Any

DATABASE_PATH = os.path.join(os.path.dirname(__file__), 'verification.db')


def init_database():
    """Initialize the SQLite database with the verification table"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS verifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            robloxUsername TEXT UNIQUE NOT NULL,
            robloxID TEXT NOT NULL,
            discordUsername TEXT NOT NULL,
            discordID TEXT NOT NULL,
            timeToVerify TEXT NOT NULL,
            joinedGame INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()


def get_connection():
    """Get a database connection"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def add_verification(roblox_username: str, roblox_id: str, discord_username: str, 
                     discord_id: str, time_to_verify: str, joined_game: bool = False) -> bool:
    """Add a new verification entry"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO verifications (robloxUsername, robloxID, discordUsername, discordID, timeToVerify, joinedGame)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (roblox_username, roblox_id, discord_username, discord_id, time_to_verify, int(joined_game)))
        
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
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
            SET robloxID = ?, discordUsername = ?, discordID = ?, timeToVerify = ?, joinedGame = ?
            WHERE robloxUsername = ?
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
        WHERE robloxUsername = ?
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
            SET joinedGame = ?
            WHERE robloxUsername = ?
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
        
        cursor.execute('DELETE FROM verifications WHERE robloxUsername = ?', (roblox_username,))
        
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
