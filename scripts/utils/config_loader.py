"""
Módulo para cargar y validar la configuración de la aplicación.

Este módulo proporciona funciones para cargar la configuración desde variables de entorno
con valores por defecto razonables y validar que la configuración sea correcta.
"""

import os
import logging
from pathlib import Path
from dotenv import load_dotenv
from typing import Dict, Any, Optional, Union

# Configuración de logging
logger = logging.getLogger(__name__)

# Directorio raíz del proyecto (tres niveles arriba de este archivo)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


def resolve_path(path: Union[str, Path], base_dir: Path = None) -> Path:
    """
    Resuelve una ruta, expande el usuario y la convierte a absoluta.
    
    Args:
        path: Ruta a resolver (puede ser relativa o absoluta)
        base_dir: Directorio base para rutas relativas. Si es None, usa PROJECT_ROOT
    
    Returns:
        Path: Ruta resuelta y normalizada
    """
    if base_dir is None:
        base_dir = PROJECT_ROOT
        
    path = Path(path).expanduser()
    if not path.is_absolute():
        path = base_dir / path
    return path.resolve()


def load_config(env_path: str = None) -> Dict[str, Any]:
    """
    Carga la configuración desde el archivo .env.
    
    La configuración se carga en este orden de prioridad:
    1. Variables de entorno del sistema
    2. Archivo .env (si existe)
    3. Valores por defecto
    
    Args:
        env_path: Ruta opcional al archivo .env. Si no se especifica,
                 busca en el directorio raíz del proyecto.
    
    Returns:
        Dict[str, Any]: Diccionario con la configuración cargada y validada.
    """
    # Cargar variables de entorno desde .env si existe
    env_file = None
    if env_path and Path(env_path).exists():
        env_file = Path(env_path).resolve()
    else:
        # Buscar .env en el directorio raíz del proyecto
        env_file = PROJECT_ROOT / '.env'
    
    if env_file.exists():
        logger.info("Cargando configuración desde: %s", env_file)
        load_dotenv(env_file, override=True)
    else:
        logger.warning("No se encontró el archivo .env. Usando variables de entorno del sistema.")
    
    # Configuración por defecto
    config = {
        # Base de datos
        'DB_PATH': os.getenv('DB_PATH', str(PROJECT_ROOT / 'data' / 'prefarm_sync.sqlite')),
        'POSTGRES_HOST': os.getenv('POSTGRES_HOST', 'localhost'),
        'POSTGRES_DB': os.getenv('POSTGRES_DB', 'chia_report'),
        'POSTGRES_USER': os.getenv('POSTGRES_USER', 'postgres'),
        'POSTGRES_PASSWORD': os.getenv('POSTGRES_PASSWORD', ''),
        'POSTGRES_PORT': int(os.getenv('POSTGRES_PORT', '5432')),
        
        # Prefarm
        'LAUNCHER_ID': os.getenv('PREFARM_LAUNCHER_ID', '6c77dce3c3bab525dab7883e8ad513a8f3ff127e872009b12836cbb1c8f26647'),
        'CHIA_ROOT': os.getenv('CHIA_ROOT', '~/.chia/mainnet'),
        'CHIA_NETWORK': os.getenv('CHIA_NETWORK', 'mainnet'),
        
        # Rutas de la aplicación
        'WEB_DATA_DIR': os.getenv('WEB_DATA_DIR', str(PROJECT_ROOT / 'data' / 'prefarm_export')),
        'LOG_LEVEL': os.getenv('LOG_LEVEL', 'INFO'),
        
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
    
    # Validar y crear directorios necesarios
    dirs_to_check = [
        ('DB_PATH', 'directorio de la base de datos', True, True),
        ('WEB_DATA_DIR', 'directorio de exportación', True, False),
    ]
    
    for dir_key, description, create_parents, is_file in dirs_to_check:
        if dir_key in config and config[dir_key]:
            try:
                path = Path(config[dir_key])
                
                # Si es un archivo, obtener el directorio padre
                if is_file:
                    dir_path = path.parent
                else:
                    dir_path = path
                
                # Resolver la ruta
                dir_path = resolve_path(dir_path)
                
                # Crear directorio si no existe
                if create_parents:
                    dir_path.mkdir(parents=True, exist_ok=True)
                
                # Verificar permisos
                if not os.access(dir_path, os.W_OK):
                    logger.warning("No se tienen permisos de escritura en el %s: %s", 
                                 description, dir_path)
                
                # Actualizar la ruta en la configuración
                if is_file:
                    config[dir_key] = str(dir_path / path.name)
                else:
                    config[dir_key] = str(dir_path)
                    
                logger.debug("%s configurado en: %s", description.capitalize(), dir_path)
                
            except Exception as e:
                logger.error("Error al configurar el %s (%s): %s", 
                            description, config[dir_key], e, exc_info=True)
                raise ValueError(f"No se pudo configurar el {description}: {e}") from e
    
    logger.info("Configuración validada correctamente")
    return True