"""
Temporary script to wipe/reset the database.
This will drop all tables and recreate them.
"""
import os
import psycopg2

# Read .env file manually
env_vars = {}
try:
    with open('.env', 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line.startswith('\ufeff'):
                line = line[1:]
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                env_vars[key.strip()] = value.strip()
except Exception as e:
    print(f"Error reading .env file: {e}")
    exit(1)

DB_USER = env_vars.get('DB_USER', 'postgres')
DB_PASSWORD = env_vars.get('DB_PASSWORD', 'admin')
DB_HOST = env_vars.get('DB_HOST', 'localhost')
DB_PORT = env_vars.get('DB_PORT', '5432')
DB_NAME = env_vars.get('DB_NAME', 'expenses_db')

import sys

print(f"Connecting to PostgreSQL as {DB_USER}@{DB_HOST}:{DB_PORT}...")
print(f"WARNING: This will DROP ALL TABLES in database '{DB_NAME}'!")

# Check for --force flag
if '--force' not in sys.argv:
    try:
        confirm = input("Type 'YES' to confirm: ")
        if confirm != 'YES':
            print("Operation cancelled.")
            exit(0)
    except EOFError:
        print("Non-interactive mode. Use --force flag to skip confirmation.")
        exit(1)
else:
    print("Force flag detected. Proceeding with database wipe...")

try:
    # Connect to PostgreSQL server
    conn = psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )
    conn.autocommit = True
    cur = conn.cursor()
    
    # Drop all tables
    print("\nDropping all tables...")
    cur.execute("""
        DO $$ DECLARE
            r RECORD;
        BEGIN
            FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname = 'public') LOOP
                EXECUTE 'DROP TABLE IF EXISTS ' || quote_ident(r.tablename) || ' CASCADE';
            END LOOP;
        END $$;
    """)
    
    print("All tables dropped successfully!")
    
    cur.close()
    conn.close()
    
    print("\nDatabase wiped. You can now restart the application to recreate tables.")
    
except psycopg2.Error as e:
    print(f"Error: {e}")
    exit(1)

