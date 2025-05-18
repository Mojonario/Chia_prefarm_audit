""
Módulo para cargar y validar la configuración de la aplicación.
"""

import os
import logging
from pathlib import Path
from dotenv import load_dotenv
from typing import Dict, Any, Optional

# Configuración de logging
logger = logging.getLogger(__name__)


def load_config(env_path: str = None) -> Dict[str, Any]:
    """
    Carga la configuración desde el archivo .env.
    
    Args:
        env_path: Ruta al archivo .env. Si es None, busca en el directorio actual.
    
    Returns:
        Dict[str, Any]: Diccionario con la configuración cargada.
    """
    # Cargar variables de entorno
    if env_path and Path(env_path).exists():
        load_dotenv(env_path)
    else:
        # Buscar .env en el directorio del proyecto
        env_file = Path(__file__).parent.parent.parent / '.env'
        if env_file.exists():
            load_dotenv(env_file)
        else:
            logger.warning("No se encontró el archivo .env. Usando variables de entorno del sistema.")
    
    # Configuración por defecto
    config = {
        # Base de datos
        'DB_PATH': os.getenv('DB_PATH', str(Path(__file__).parent.parent.parent / 'prefarm_sync.sqlite')),
        'POSTGRES_HOST': os.getenv('POSTGRES_HOST', 'localhost'),
        'POSTGRES_DB': os.getenv('POSTGRES_DB', 'chia_report'),
        'POSTGRES_USER': os.getenv('POSTGRES_USER', 'postgres'),
        'POSTGRES_PASSWORD': os.getenv('POSTGRES_PASSWORD', ''),
        'POSTGRES_PORT': int(os.getenv('POSTGRES_PORT', '5432')),
        
        # Prefarm
        'LAUNCHER_ID': os.getenv('PREFARM_LAUNCHER_ID', '6c77dce3c3bab525dab7883e8ad513a8f3ff127e872009b12836cbb1c8f26647'),
        'CHIA_ROOT': os.getenv('CHIA_ROOT', '~/.chia/mainnet'),
        'CHIA_NETWORK': os.getenv('CHIA_NETWORK', 'mainnet'),
        
        # Web
        'WEB_DATA_DIR': os.getenv('WEB_DATA_DIR', str(Path(__file__).parent.parent.parent.parent / 'Chia.report' / 'prefarm_data')),
        
        # Monitoreo
        'POLL_INTERVAL': int(os.getenv('POLL_INTERVAL', '300')),  # segundos
    }
    
    # Validar la configuración
    validate_config(config)
    
    return config

def validate_config(config: Dict[str, Any]) -> bool:
    """
    Valida la configuración cargada.
    
    Args:
        config: Diccionario con la configuración a validar.
    
    Returns:
        bool: True si la configuración es válida, False en caso contrario.
    
    Raises:
        ValueError: Si la configuración no es válida.
    """
    required_vars = [
        'LAUNCHER_ID',
    ]
    
    missing_vars = [var for var in required_vars if not config.get(var)]
    
    if missing_vars:
        error_msg = f"Faltan variables de entorno requeridas: {', '.join(missing_vars)}"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    # Validar formato del LAUNCHER_ID (debe ser un hash de 64 caracteres hexadecimales)
    if not all(c in '0123456789abcdef' for c in config['LAUNCHER_ID'].lower()) or len(config['LAUNCHER_ID']) != 64:
        error_msg = f"LAUNCHER_ID no válido. Debe ser un hash de 64 caracteres hexadecimales."
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    # Validar directorios
    for dir_key in ['WEB_DATA_DIR']:
        if dir_key in config and config[dir_key]:
            try:
                dir_path = Path(config[dir_key])
                dir_path.mkdir(parents=True, exist_ok=True)
                if not os.access(dir_path, os.W_OK):
                    logger.warning(f"No se tienen permisos de escritura en el directorio: {dir_path}")
            except Exception as e:
                logger.warning(f"No se pudo crear/validar el directorio {dir_key}: {e}")
    
    logger.info("Configuración validada correctamente")
    return True