# 🚜 Chia Prefarm Audit Tools

> Herramienta para auditar y monitorear transacciones del prefarm de Chia

[![Python Version](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 📋 Descripción

Este proyecto proporciona un flujo completo para auditar y procesar las transacciones de la hot wallet del prefarm de Chia, incluyendo:

- 🔄 Sincronización del estado de la wallet (usando `cic sync`)
- 🔍 Auditoría y extracción de transacciones HANDLE_PAYMENT a CSV
- 📊 Procesamiento de resúmenes de transacciones
- 💾 Almacenamiento en PostgreSQL para análisis histórico
- 📁 Exportación de datos a formato CSV

## 🎯 Características

- **Automatización completa** - Proceso de extremo a extremo con un solo comando
- **Configuración flexible** - Personalizable a través de variables de entorno
- **Registro detallado** - Logs informativos para seguimiento y depuración
- **Base de datos centralizada** - Almacenamiento estructurado para análisis histórico
- **Portable** - Funciona en Windows, macOS y Linux

## 📋 Requisitos

- Python 3.9 o superior
- PostgreSQL 12+ (o servicio compatible como AWS RDS, Render, etc.)
- Nodo Chia completo sincronizado (con RPC habilitado en `localhost:8555`)
- Git (para clonar el repositorio)

## 🚀 Instalación Rápida

1. **Clonar el repositorio**
   ```bash
   git clone https://github.com/Mojonario/Chia_prefarm_audit.git
   cd Chia_prefarm_audit
   ```

2. **Configurar entorno virtual**
   ```bash
   # Windows
   python -m venv venv
   .\venv\Scripts\activate
   
   # Linux/macOS
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Instalar dependencias**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configurar variables de entorno**
   ```bash
   # Copiar el archivo de ejemplo
   copy .env.example .env
   ```
   
   Luego editar `.env` con tus configuraciones:
   ```env
   # Configuración de la base de datos PostgreSQL
   DATABASE_URL=postgresql://usuario:contraseña@localhost:5432/chia_report
   
   # Directorio para exportar los archivos CSV
   WEB_DATA_DIR=./data/exports
   
   # Configuración del nodo Chia
   CHIA_ROOT=~/.chia/mainnet
   CHIA_NETWORK=mainnet
   
   # Nivel de log (DEBUG, INFO, WARNING, ERROR, CRITICAL)
   LOG_LEVEL=INFO
   ```

## 🛠️ Uso

### Ejecutar la auditoría completa

```bash
python scripts/update_prefarmdb.py
```

## 📁 Estructura del Proyecto

```
Chia_prefarm_audit/
├── .env                    # Configuración de entorno (no versionado)
├── .env.example            # Plantilla de configuración
├── scripts/                # Scripts principales
│   ├── update_prefarmdb.py # Script principal de actualización
│   ├── cic_audit_helper.py # Funciones de ayuda para auditoría
│   ├── ingest_prefarmdb.py # Funciones para ingesta en la base de datos
│   └── utils/              # Utilidades
│       ├── config_loader.py # Cargador de configuración
│       └── db_connector.py # Conexión a bases de datos
├── csv/                    # Archivos CSV generados (no versionados)
├── sync/                   # Base de datos de sincronización SQLite (no versionada)
└── internal-custody/       # Configuraciones de custodia
    └── prefarm_configs/    # Archivos de configuración para diferentes prefarms
        ├── warm-us-public-config.txt  # Configuración para prefarm US
        └── ...
```

### 📂 Directorios Importantes

- `scripts/`: Contiene todo el código fuente de la aplicación
- `csv/`: Almacena los informes de auditoría en formato CSV
- `sync/`: Base de datos SQLite para sincronización local
- `internal-custody/`: Configuraciones específicas para diferentes prefarms

## ⚙️ Configuración de Variables de Entorno

El proyecto utiliza un archivo `.env` para la configuración. Copia `.env.example` a `.env` y ajusta los valores según sea necesario.

### 🔑 Variables Requeridas

| Variable | Valor por Defecto | Descripción |
|----------|-------------------|-------------|
| `DATABASE_URL` | - | URL de conexión a PostgreSQL en formato `postgresql://usuario:contraseña@host:puerto/base_de_datos` |
| `WEB_DATA_DIR` | `./data/exports` | Directorio donde se guardarán los informes CSV |
| `CHIA_ROOT` | `~/.chia/mainnet` | Ruta al directorio de instalación de Chia |
| `PREFARM_LAUNCHER_ID` | - | ID del launcher del prefarm a auditar |

### 🔧 Variables Opcionales

| Variable | Valor por Defecto | Descripción |
|----------|-------------------|-------------|
| `CHIA_NETWORK` | `mainnet` | Red de Chia (`mainnet` o `testnet`) |
| `LOG_LEVEL` | `INFO` | Nivel de detalle de los logs (`DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`) |
| `DB_PATH` | `./data/prefarm_sync.sqlite` | Ruta a la base de datos SQLite local |

### 🔄 Sincronización con el Nodo Chia

Asegúrate de que tu nodo Chia esté sincronizado y que el RPC esté habilitado en `localhost:8555` para que la herramienta pueda comunicarse con él.

## 🛠️ Uso Avanzado

### Ejecutar con opciones personalizadas

Puedes sobrescribir cualquier configuración desde la línea de comandos:

```bash
# Ejecutar con nivel de depuración
LOG_LEVEL=DEBUG python scripts/update_prefarmdb.py

# Especificar un directorio de salida personalizado
WEB_DATA_DIR=/ruta/personalizada python scripts/update_prefarmdb.py
```

### Programar ejecución automática

Para ejecutar la auditoría periódicamente (por ejemplo, cada hora), puedes usar `cron` en Linux/macOS o el Programador de tareas en Windows.

**Ejemplo con cron (Linux/macOS):**

```bash
# Editar el crontab
crontab -e

# Agregar esta línea para ejecutar cada hora
0 * * * * cd /ruta/a/chia_prefarm_audit && . venv/bin/activate && python scripts/update_prefarmdb.py >> ~/chia_audit.log 2>&1
```

### Solución de Problemas Comunes

#### Error de conexión al nodo Chia

```
Error: No se puede conectar al nodo Chia en localhost:8555
```

Solución:
1. Verifica que el nodo Chia esté en ejecución
2. Asegúrate de que el RPC esté habilitado en `~/.chia/mainnet/config/config.yaml`:
   ```yaml
   rpc_port: 8555
   rpc_allow_private_subnet: true
   ```
3. Reinicia el nodo Chia después de los cambios

#### Problemas con la base de datos

Si necesitas reiniciar la sincronización desde cero:

```bash
# Detener cualquier proceso en ejecución
rm -rf sync/*.sqlite  # Elimina las bases de datos de sincronización
```

## 📊 Visualización de Datos

Los datos de auditoría se pueden visualizar usando herramientas como:

- **Metabase**: Para crear dashboards interactivos
- **Grafana**: Para monitoreo en tiempo real
- **Excel/Power BI**: Para análisis avanzado

Ejemplo de consulta SQL para obtener el saldo actual:

```sql
SELECT 
    date_trunc('day', timestamp) AS fecha,
    SUM(amount) AS balance_diario
FROM prefarmdb
WHERE timestamp > NOW() - INTERVAL '30 days'
GROUP BY 1
ORDER BY 1;
```

## 🤝 Contribución

Las contribuciones son bienvenidas. Por favor, lee [CONTRIBUTING.md](CONTRIBUTING.md) para más detalles.

## 📄 Licencia

Este proyecto está bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para más detalles.

---

Desarrollado con ❤️ por el equipo de Chia.report
```bash
cd /home/<usuario>/chia_prefarm_audit  # ir a la carpeta del proyecto
python3 -m venv venv
source venv/bin/activate
```

4. Instalar dependencias:

```bash
pip install --upgrade pip setuptools wheel
pip install chia-internal-custody
pip install -r requirements.txt
```

## Uso

### Crear tabla en PostgreSQL

```bash
python scripts/init_prefarmdb.py
```

### Flujo completo de actualización

```bash
python scripts/update_prefarmdb.py
```

Este script ejecuta:

1. `cic sync` y `cic audit` para la hot wallet.
2. Procesa `csv/warm_us_audit.csv` a `csv/warm_us_summary.csv`.
3. Copia el resumen a la carpeta definida por `WEB_DATA_DIR`.
4. Ingiere los datos en la tabla `prefarmdb` de PostgreSQL.

### Solo ingestión (tienes el summary CSV)

```bash
python scripts/ingest_prefarmdb.py -s csv/warm_us_summary.csv
```

## Estructura del proyecto

```
chia_prefarm_audit/
├── .env                # Variables reales (no versionar)
├── requirements.txt    # Dependencias pip
├── create_prefarmdb.sql# DDL de la tabla prefarmdb
├── csv/                # Archivos CSV (raw y summary)
│   ├── warm_us_audit.csv
│   └── warm_us_summary.csv
├── sync/               # sync_warm_us.sqlite (DB local cic)
├── internal-custody/   # Submódulo con configs de cic
├── scripts/            # Scripts Python ejecutables
│   ├── init_prefarmdb.py
│   ├── cic_audit_helper.py
│   ├── ingest_prefarmdb.py
│   └── update_prefarmdb.py
└── venv/               # Entorno virtual
```

## Variables de entorno

| Variable         | Descripción                                  |
|------------------|----------------------------------------------|
| DATABASE_URL     | Cadena de conexión a PostgreSQL              |
| PREFARM_CIC_CONFIG| Ruta al config de `cic` (opcional)         |
| WEB_DATA_DIR     | Directorio para copiar el resumen (opcional) |

## Licencia

MIT
