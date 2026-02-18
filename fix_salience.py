"""
Quick fix for salience=None bug in existing database
Run this once to fix old data
"""

import sys
from pathlib import Path

ROOT_DIR = Path("c:/Users/Notandi/Desktop/agi/engram-system")
sys.path.append(str(ROOT_DIR))

from core.storage import EngramStorage

print("🔧 Fixing salience=None in database...")

storage = EngramStorage()

# Update all None salience values to 1.0
cursor = storage.conn.execute("""
    UPDATE abstractions 
    SET salience = 1.0 
    WHERE salience IS NULL
""")

rows_updated = cursor.rowcount
storage.conn.commit()

print(f"✅ Fixed {rows_updated} abstractions with missing salience values")
print("Database is now ready!")
