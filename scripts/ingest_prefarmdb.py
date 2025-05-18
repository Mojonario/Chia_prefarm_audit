#!/usr/bin/env python3
"""
Ingest processed hot wallet CSV into Postgres table prefarmdb.
Requires DATABASE_URL env var and a CSV with columns time,amount_xch.
"""
import os
import sys
import csv
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()
import psycopg2
from psycopg2.extras import execute_values
import logging
from decimal import Decimal

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

def connect_db(url):
    return psycopg2.connect(url)

def ingest_file(summary_csv_path: str, table: str = 'prefarmdb'):
    path = Path(summary_csv_path)
    if not path.exists():
        logger.error("Summary CSV not found: %s", path)
        raise FileNotFoundError(f"Summary CSV not found: {path}")
    # Leer CSV
    with path.open(newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        records = []
        for row in reader:
            date = row.get('time')
            amt_str = row.get('amount_xch')
            if date and amt_str:
                try:
                    amount = Decimal(amt_str)
                except Exception:
                    logger.warning("Invalid amount '%s' on date %s, skipping", amt_str, date)
                    continue
                records.append((date, amount))
    if not records:
        logger.info("No records to ingest for file %s", path)
        return 0
    # Conectar DB
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        logger.error("DATABASE_URL env var not set")
        raise EnvironmentError("DATABASE_URL env var not set")
    conn = connect_db(db_url)
    cur = conn.cursor()
    # Crear tabla si no existe
    cur.execute(f"""
        CREATE TABLE IF NOT EXISTS {table} (
            time DATE PRIMARY KEY,
            amount_xch NUMERIC(20,12) NOT NULL
        );
    """)
    # Insertar filas (ignorar duplicados)
    insert_sql = f"INSERT INTO {table} (time, amount_xch) VALUES %s ON CONFLICT (time) DO NOTHING"
    execute_values(cur, insert_sql, records)
    conn.commit()
    logger.info("Ingested %d rows into '%s' (duplicates skipped by PK)", len(records), table)
    cur.close()
    conn.close()
    return len(records)

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Ingest hot wallet summary CSV into Postgres')
    parser.add_argument('-s', '--summary', required=True, help='Path to summary CSV file')
    parser.add_argument('-t', '--table', default='prefarmdb', help='Target table name')
    args = parser.parse_args()
    if not os.getenv('DATABASE_URL'):
        logger.error('DATABASE_URL env var not set')
        sys.exit(1)
    try:
        count = ingest_file(args.summary, args.table)
        logger.info('Ingestion completed, %d rows processed', count)
        sys.exit(0)
    except Exception as e:
        logger.error('Error ingesting file: %s', e)
        sys.exit(1)
