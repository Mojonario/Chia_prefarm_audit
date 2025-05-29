#!/usr/bin/env python3
"""
Orquesta todo el flujo: sync/audit, procesa CSV, copia resumen y lo ingesta en Postgres.
"""
import os
import shutil
import sys
from pathlib import Path
import subprocess
import logging

# Configuración de rutas
project_root = Path(__file__).resolve().parent.parent

# Añadir carpeta scripts al PATH para importar módulos locales
scripts_dir = project_root / 'scripts'
sys.path.insert(0, str(scripts_dir))

# Configuración básica de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

# Cargar configuración
try:
    from utils.config_loader import load_config
    config = load_config()
    logger.setLevel(getattr(logging, config.get('LOG_LEVEL', 'INFO')))
except ImportError as e:
    logger.error("Error al cargar la configuración: %s", e)
    sys.exit(1)

# Importar módulos locales
try:
    from cic_audit_helper import get_cic_executable, audit_wallet, process_audit_csv
    from ingest_prefarmdb import ingest_file
except ImportError as e:
    logger.error("Error al importar módulos locales: %s", e)
    sys.exit(1)

def main():
    """Función principal que orquesta el proceso de actualización."""
    # Configuración inicial
    project_root = Path(__file__).parent.parent

    # Rutas y configuración
    # Config and DB path (always use sync folder)
    config_file = project_root / 'internal-custody' / 'prefarm_configs' / 'warm-us-public-config.txt'
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
    # Usamos el archivo de configuración directamente en lugar del diccionario
    config_file = project_root / 'internal-custody' / 'prefarm_configs' / 'warm-us-public-config.txt'
    logger.info("🔄 Running cic sync with config=%s, db=%s", config_file, db_path)
    try:
        subprocess.run([cic, 'sync', '-c', str(config_file), '-db', str(db_path)], check=True)
        logger.info("✅ cic sync completed")
    except subprocess.CalledProcessError as e:
        logger.error("❌ Error al ejecutar cic sync: %s", e)
        return
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
    # Obtener directorio de destino de la configuración
    dest_dir = os.getenv('WEB_DATA_DIR', str(project_root / 'data' / 'prefarm_export'))
    dest_dir = Path(dest_dir).resolve()  # Convertir a ruta absoluta
    
    # Mostrar información de depuración
    logger.debug("Directorio de destino: %s", dest_dir)
    
    # Verificar si el directorio existe, si no, crearlo
    if not dest_dir.exists():
        logger.info("El directorio %s no existe. Se creará automáticamente.", dest_dir)
    
    # Asegurarse de que el directorio exista
    try:
        dest_dir.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        logger.error('No se pudo crear el directorio %s: %s', dest_dir, str(e))
        sys.exit(1)
    
    # Crear la ruta completa del archivo de destino
    dest_file = dest_dir / summary_path.name
    
    # Verificar permisos del directorio de destino
    if not os.access(str(dest_dir), os.W_OK):
        logger.error('No se tienen permisos de escritura en el directorio de destino: %s', dest_dir)
        sys.exit(1)
    
    # Copiar el archivo
    try:
        # Usar una ruta absoluta para el archivo de origen
        src_path = str(summary_path.resolve())
        dst_path = str(dest_file)
        
        # Debug: Mostrar rutas de origen y destino
        logger.info("Copiando desde: %s", src_path)
        logger.info("Copiando a: %s", dst_path)
        
        # Verificar que el archivo fuente existe
        if not os.path.exists(src_path):
            logger.error('El archivo fuente no existe: %s', src_path)
            sys.exit(1)
            
        # Copiar el archivo
        shutil.copy2(src_path, dst_path)
        
        # Verificar que el archivo se copió correctamente
        if not os.path.exists(dst_path):
            logger.error('Error al copiar el archivo a: %s', dst_path)
            sys.exit(1)
            
        logger.info('📁 Summary CSV copiado correctamente a: %s', dst_path)
        
    except Exception as e:
        logger.error('Error al copiar el archivo CSV: %s', str(e))
        logger.exception('Detalles del error:')
        sys.exit(1)

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
