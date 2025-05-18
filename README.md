# Chia Prefarm Audit Tools

Este proyecto proporciona un flujo completo para auditar y procesar las transacciones de la hot wallet del prefarm de Chia:

- Sincroniza el estado de la wallet (usando `cic sync`).
- Audita y extrae transacciones de tipo HANDLE_PAYMENT a CSV.
- Procesa un resumen de transacciones (`warm_us_summary.csv`).
- Copia el resumen al directorio configurado por `WEB_DATA_DIR` (por ejemplo `C:\Users\<usuario>\Directorio\carpeta` en Windows o `/home/<usuario>/Directorio/carpeta` en Linux).
- Carga los datos en PostgreSQL en la tabla `prefarmdb`.

Objetivo: facilitar el seguimiento y análisis histórico de los movimientos de prefarm, integrando auditoría, procesamiento y almacenamiento en un único flujo automatizado.

## Requisitos

- Git
- Python 3.9+
- PostgreSQL (o un servicio compatible)
- Nodo Chia completo sincronizado (RPC abierto en localhost:8555)

## Instalación

1. Clonar el repositorio:

```bash
git clone https://github.com/Mojonario/Chia_prefarm_audit.git chia_prefarm_audit
cd C:\Users\<usuario>\chia_prefarm_audit  # ir a la carpeta del proyecto
```

2. Configurar variables de entorno:

Crear `.env` con (reemplaza valores y ruta según tu entorno):

```env
DATABASE_URL=postgresql://<user>:<pass>@<host>:<port>/<db>
# Directorio donde copiar el CSV resumido
WEB_DATA_DIR=C:\Users\<usuario>\Directorio\carpeta
```

3. Crear y activar entorno virtual:

- Windows (PowerShell):

```powershell
cd C:\Users\<usuario>\chia_prefarm_audit  # ir a la carpeta del proyecto
python -m venv venv
.\venv\Scripts\Activate.ps1
```

- Ubuntu/Linux (bash):

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
