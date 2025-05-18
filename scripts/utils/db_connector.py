"""
Módulo para la conexión a bases de datos SQLite y PostgreSQL.
"""

import os
import sqlite3
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import psycopg2
from psycopg2.extras import DictCursor

# Configuración de logging
logger = logging.getLogger(__name__)

def get_db_connection(db_type: str = 'sqlite', **kwargs):
    """
    Establece y devuelve una conexión a la base de datos.
    
    Args:
        db_type: Tipo de base de datos ('sqlite' o 'postgresql').
        **kwargs: Parámetros adicionales para la conexión.
            Para SQLite: db_path (str)
            Para PostgreSQL: host, database, user, password, port
    
    Returns:
        Conexión a la base de datos.
    
    Raises:
        ValueError: Si el tipo de base de datos no es compatible.
        Exception: Si no se puede establecer la conexión.
    """
    try:
        if db_type.lower() == 'sqlite':
            db_path = kwargs.get('db_path', str(Path(__file__).parent.parent.parent / 'prefarm_sync.sqlite'))
            
            # Asegurarse de que el directorio existe
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
            
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row  # Para acceder a las columnas por nombre
            logger.debug(f"Conexión a SQLite establecida: {db_path}")
            
        elif db_type.lower() in ['postgres', 'postgresql']:
            conn = psycopg2.connect(
                host=kwargs.get('host', 'localhost'),
                database=kwargs.get('database', 'chia_report'),
                user=kwargs.get('user', 'postgres'),
                password=kwargs.get('password', ''),
                port=kwargs.get('port', 5432),
                cursor_factory=DictCursor
            )
            logger.debug("Conexión a PostgreSQL establecida")
            
        else:
            raise ValueError(f"Tipo de base de datos no soportado: {db_type}")
        
        return conn
        
    except Exception as e:
        logger.error(f"Error al conectar a la base de datos {db_type}: {e}")
        raise

def execute_query(conn, query: str, params: tuple = None, fetch: bool = True):
    """
    Ejecuta una consulta SQL y devuelve los resultados.
    
    Args:
        conn: Conexión a la base de datos.
        query: Consulta SQL a ejecutar.
        params: Parámetros para la consulta.
        fetch: Si es True, devuelve los resultados de la consulta.
    
    Returns:
        Resultados de la consulta si fetch=True, de lo contrario None.
    """
    cursor = None
    try:
        cursor = conn.cursor()
        
        # Ejecutar la consulta
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        
        # Confirmar los cambios
        conn.commit()
        
        # Devolver resultados si es necesario
        if fetch and cursor.description:
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
        elif not fetch:
            return None
        else:
            return cursor.fetchall()
            
    except Exception as e:
        logger.error(f"Error al ejecutar la consulta: {e}")
        if conn:
            conn.rollback()
        raise
    finally:
        if cursor:
            cursor.close()

def fetch_all(conn, table: str, columns: list = None, where: str = None, 
              params: tuple = None, order_by: str = None, limit: int = None):
    """
    Obtiene todos los registros de una tabla.
    
    Args:
        conn: Conexión a la base de datos.
        table: Nombre de la tabla.
        columns: Lista de columnas a seleccionar (todas si es None).
        where: Condición WHERE opcional.
        params: Parámetros para la condición WHERE.
        order_by: Ordenación opcional.
        limit: Límite de registros a devolver.
    
    Returns:
        Lista de diccionarios con los resultados.
    """
    # Construir la consulta SELECT
    cols = ', '.join(columns) if columns else '*'
    query = f"SELECT {cols} FROM {table}"
    
    # Añadir condiciones WHERE
    if where:
        query += f" WHERE {where}"
    
    # Añadir ordenación
    if order_by:
        query += f" ORDER BY {order_by}"
    
    # Añadir límite
    if limit is not None:
        query += f" LIMIT {int(limit)}"
    
    # Ejecutar la consulta
    return execute_query(conn, query, params)

def insert_record(conn, table: str, data: dict) -> int:
    """
    Inserta un registro en una tabla.
    
    Args:
        conn: Conexión a la base de datos.
        table: Nombre de la tabla.
        data: Diccionario con los datos a insertar (columna: valor).
    
    Returns:
        ID del registro insertado.
    """
    if not data:
        raise ValueError("No se proporcionaron datos para insertar")
    
    columns = ', '.join(data.keys())
    placeholders = ', '.join(['%s'] * len(data))
    values = tuple(data.values())
    
    query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
    
    # Para SQLite, necesitamos manejar el retorno del ID de manera diferente
    if isinstance(conn, sqlite3.Connection):
        query += " RETURNING id"
        result = execute_query(conn, query, values)
        return result[0]['id'] if result else None
    else:
        # Para PostgreSQL
        query += " RETURNING id"
        cursor = conn.cursor()
        try:
            cursor.execute(query, values)
            conn.commit()
            return cursor.fetchone()[0]
        except Exception as e:
            conn.rollback()
            raise
        finally:
            cursor.close()

def update_record(conn, table: str, data: dict, where: str, params: tuple = None) -> int:
    """
    Actualiza registros en una tabla.
    
    Args:
        conn: Conexión a la base de datos.
        table: Nombre de la tabla.
        data: Diccionario con los datos a actualizar (columna: valor).
        where: Condición WHERE para identificar los registros a actualizar.
        params: Parámetros adicionales para la condición WHERE.
    
    Returns:
        Número de filas afectadas.
    """
    if not data:
        raise ValueError("No se proporcionaron datos para actualizar")
    
    set_clause = ', '.join([f"{k} = %s" for k in data.keys()])
    values = tuple(data.values())
    
    # Combinar con los parámetros de la condición WHERE si los hay
    if params:
        values += tuple(params)
    
    query = f"UPDATE {table} SET {set_clause} WHERE {where}"
    
    cursor = conn.cursor()
    try:
        cursor.execute(query, values)
        conn.commit()
        return cursor.rowcount
    except Exception as e:
        conn.rollback()
        logger.error(f"Error al actualizar registro: {e}")
        raise
    finally:
        cursor.close()