from app import app, db
from models import User, Surat, PengajuanSurat, LoginHistory, ResetPasswordRequest
import sqlite3
import os

def fix_database():
    with app.app_context():
        # Check if whatsapp column exists in user table
        conn = sqlite3.connect('instance/db.sqlite3')
        cursor = conn.cursor()
        
        # Get table info
        cursor.execute("PRAGMA table_info(user)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'whatsapp' not in columns:
            print("Adding whatsapp column to user table...")
            try:
                cursor.execute("ALTER TABLE user ADD COLUMN whatsapp VARCHAR(20)")
                conn.commit()
                print("✅ whatsapp column added successfully!")
            except Exception as e:
                print(f"❌ Error adding column: {e}")
        else:
            print("✅ whatsapp column already exists")
        
        conn.close()

if __name__ == '__main__':
    fix_database() 