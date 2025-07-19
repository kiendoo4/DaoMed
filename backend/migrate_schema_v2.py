#!/usr/bin/env python3
"""
Migration script to add max_chunks and cosine_threshold columns to dialogs table
"""

import psycopg2
import json
from app.config import Config

def migrate_dialogs_schema():
    """Add max_chunks and cosine_threshold columns to dialogs table"""
    
    conn = psycopg2.connect(
        host=Config.POSTGRES_HOST,
        database=Config.POSTGRES_DB,
        user=Config.POSTGRES_USER,
        password=Config.POSTGRES_PASSWORD,
        port=Config.POSTGRES_PORT
    )
    
    cur = conn.cursor()
    
    try:
        # Check if columns already exist
        cur.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'dialogs' 
            AND column_name IN ('max_chunks', 'cosine_threshold')
        """)
        existing_columns = [row[0] for row in cur.fetchall()]
        
        # Add max_chunks column if not exists
        if 'max_chunks' not in existing_columns:
            print("Adding max_chunks column...")
            cur.execute("""
                ALTER TABLE dialogs 
                ADD COLUMN max_chunks INTEGER DEFAULT 8
            """)
            print("✅ Added max_chunks column with default value 8")
        
        # Add cosine_threshold column if not exists
        if 'cosine_threshold' not in existing_columns:
            print("Adding cosine_threshold column...")
            cur.execute("""
                ALTER TABLE dialogs 
                ADD COLUMN cosine_threshold FLOAT DEFAULT 0.5
            """)
            print("✅ Added cosine_threshold column with default value 0.5")
        
        # Update existing dialogs to have default values
        cur.execute("""
            UPDATE dialogs 
            SET max_chunks = 8, cosine_threshold = 0.5
            WHERE max_chunks IS NULL OR cosine_threshold IS NULL
        """)
        
        # Update model_config for existing dialogs to include new models
        cur.execute("SELECT id, model_config FROM dialogs")
        dialogs = cur.fetchall()
        
        new_models = [
            "gemini-2.0-flash",
            "gemini-2.0-flash-thinking-mode", 
            "gemini-2.0-flash-lite",
            "gemini-2.5-flash",
            "gemini-2.5-flash-lite"
        ]
        
        for dialog_id, model_config in dialogs:
            if model_config:
                config = model_config if isinstance(model_config, dict) else json.loads(model_config)
                # Update model if it's the old one
                if config.get('model') == 'gemini-2.0-flash-exp':
                    config['model'] = 'gemini-2.0-flash'
                    cur.execute("""
                        UPDATE dialogs 
                        SET model_config = %s
                        WHERE id = %s
                    """, (json.dumps(config), dialog_id))
                    print(f"✅ Updated dialog {dialog_id} model to gemini-2.0-flash")
        
        conn.commit()
        print("🎉 Migration completed successfully!")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Migration failed: {e}")
        raise
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    print("🔄 Starting dialogs schema migration...")
    migrate_dialogs_schema()
    print("✅ Migration finished!") 