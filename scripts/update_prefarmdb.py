#!/usr/bin/env python3
"""
Orquesta todo el flujo: sync/audit, procesa CSV, copia resumen y lo ingesta en Postgres.
"""
import os
import shutil
import sys
from pathlib import Path
from dotenv import load_dotenv
import subprocess
import logging

# Carga variables desde .env
project_root = Path(__file__).resolve().parent.parent
env_path = project_root / '.env'
load_dotenv(env_path)

# Añadir carpeta scripts al PATH para importar módulos locales
scripts_dir = project_root / 'scripts'
sys.path.insert(0, str(scripts_dir))

from cic_audit_helper import get_cic_executable, audit_wallet, process_audit_csv
from ingest_prefarmdb import ingest_file

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

def main():
    # Rutas y configuración
    # Config and DB path (always use sync folder)
    config = project_root / 'internal-custody' / 'prefarm_configs' / 'warm-us-public-config.txt'
    db_path = project_root / 'sync' / 'sync_warm_us.sqlite'
    audit_csv = project_root / 'csv' / 'warm_us_audit.csv'
    summary_csv = project_root / 'csv' / 'warm_us_summary.csv'

    # 1. Preparar y ejecutar cic sync y audit
    db_file = Path(db_path)
    # Ensure sync directory exists
    db_file.parent.mkdir(parents=True, exist_ok=True)
    if db_file.exists():
        logger.info("Removing existing sync DB: %s", db_file)
        db_file.unlink()
    cic = get_cic_executable()
    logger.info("🔄 Running cic sync with config=%s, db=%s", config, db_path)
    subprocess.run([cic, 'sync', '-c', str(config), '-db', str(db_path)], check=True)
    logger.info("🔄 cic sync completed")
    logger.info("📊 Running cic audit, output=%s", audit_csv)
    subprocess.run([cic, 'audit', '-db', str(db_path), '-f', str(audit_csv)], check=True)
    logger.info("📊 cic audit completed, raw CSV at %s", audit_csv)
    # 2. Procesar CSV de auditoría
    logger.info("🔎 Processing audit CSV to summary")
    process_audit_csv(str(audit_csv), str(summary_csv))
    summary_path = summary_csv
    with summary_path.open('r', encoding='utf-8') as f:
        total = sum(1 for _ in f) - 1
    logger.info("🔢 Found %d summary records", total)

    # 2. Copiar CSV procesado a carpeta de datos web
    # Determinar directorio destino usando solo WEB_DATA_DIR
    web_dir = os.getenv('WEB_DATA_DIR')
    if not web_dir:
        logger.info(
            "La variable de entorno WEB_DATA_DIR no está definida en .env. "
            "Por favor añade WEB_DATA_DIR a tu .env (e.g. C:\\Users\\<usuario>\\Directorio\\carpeta o /home/<usuario>/Directorio/carpeta)."
        )
        sys.exit(1)
    dest_dir = Path(web_dir)
    if not dest_dir.exists():
        logger.info("El directorio %s no existe. Se creará automáticamente.", dest_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_file = dest_dir / summary_path.name
    logger.debug('Copying summary CSV to %s', dest_file)
    try:
        shutil.copy2(summary_path, dest_file)
    except Exception as e:
        logger.error('Failed to copy summary CSV: %s', e)
        sys.exit(1)
    logger.info('📁 Summary CSV copied to %s', dest_file)

    # 3. Ingestar en Postgres
    logger.info('🗄️ Ingesting data into table prefarmdb')
    try:
        ingest_file(str(dest_file))
    except Exception as e:
        logger.error('Error ingesting file: %s', e)
        sys.exit(1)

    logger.info('✅ Update flow completed.')

if __name__ == '__main__':
    main()
