#!/usr/bin/env python3
"""
Migration script to add system_prompt and model_config columns to dialogs table
"""
import psycopg2
import json
from app.config import Config

def migrate_dialogs_table():
    """Add system_prompt and model_config columns to dialogs table"""
    conn = psycopg2.connect(
        host=Config.POSTGRES_HOST,
        port=Config.POSTGRES_PORT,
        database=Config.POSTGRES_DB,
        user=Config.POSTGRES_USER,
        password=Config.POSTGRES_PASSWORD
    )
    
    cur = conn.cursor()
    
    try:
        # Check if columns already exist
        cur.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'dialogs' 
            AND column_name IN ('system_prompt', 'model_config')
        """)
        existing_columns = [row[0] for row in cur.fetchall()]
        
        # Add system_prompt column if not exists
        if 'system_prompt' not in existing_columns:
            print("Adding system_prompt column...")
            cur.execute("""
                ALTER TABLE dialogs 
                ADD COLUMN system_prompt TEXT DEFAULT 'You are a knowledgeable and helpful chatbot specializing in Traditional Eastern Medicine.'
            """)
        
        # Add model_config column if not exists
        if 'model_config' not in existing_columns:
            print("Adding model_config column...")
            default_config = json.dumps({
                "model": "gemini-2.0-flash-exp",
                "temperature": 0.7,
                "max_tokens": 1000
            })
            cur.execute(f"""
                ALTER TABLE dialogs 
                ADD COLUMN model_config JSONB DEFAULT '{default_config}'::jsonb
            """)
        
        conn.commit()
        print("✅ Migration completed successfully!")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Migration failed: {str(e)}")
        raise
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    print("🔄 Starting database migration...")
    migrate_dialogs_table() 