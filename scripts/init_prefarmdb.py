#!/usr/bin/env python3
"""
Crea la tabla prefarmdb en Postgres usando create_prefarmdb.sql.
"""
import os
from pathlib import Path
from dotenv import load_dotenv
import psycopg2

# Carga variables de .env
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

# Leer SQL
def_file = Path(__file__).parent.parent / 'create_prefarmdb.sql'
sql = def_file.read_text(encoding='utf-8')

# Conexión y ejecución
url = os.getenv('DATABASE_URL')
if not url:
    print('Error: DATABASE_URL no está definido en .env')
    exit(1)
conn = psycopg2.connect(url)
cur = conn.cursor()
cur.execute(sql)
conn.commit()
cur.close()
conn.close()
print('Tabla prefarmdb creada/existe.')
