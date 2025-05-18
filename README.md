# Chia Prefarm Audit Tools

Herramientas para auditar y monitorear las billeteras del prefarm de Chia.

## Requisitos

- Python 3.9+
- Nodo Chia completo sincronizado
- Dependencias: `pip install -r requirements.txt`

## Herramientas

### 1. Verificación de Saldos

Verifica los saldos actuales de las direcciones del prefarm.

```bash
python scripts/check_prefarm_balances.py
```

Ejemplo de salida:
```
=== SALDOS DEL PREFARM CHIA ===
----------------------------------------
Cold US:
  Dirección: xch1jj0gm4ahhlu3ke0r0fx955v8axr6za7rzz6hc0y26lewa7zw6fws5nwvv6
  Saldo: 1,234,567.890123 XCH

...
----------------------------------------
SALDO TOTAL: 4,567,890.123456 XCH
========================================
```

### 2. Monitoreo de Transacciones

Monitorea transacciones en tiempo real en las direcciones del prefarm.

```bash
python scripts/monitor_transactions.py
```

### 3. Utilidad de Direcciones

Convierte entre direcciones y puzzle hashes.

```bash
# De dirección a puzzle hash
python scripts/address_utils.py to-puzzle-hash xch1jj0gm4ahhlu3ke0r0fx955v8axr6za7rzz6hc0y26lewa7zw6fws5nwvv6

# De puzzle hash a dirección
python scripts/address_utils.py to-address 0x1234... --prefix xch
```

## Configuración

### Variables de Entorno

Crea un archivo `.env` en la raíz del proyecto:

```env
# Configuración del nodo Chia
NODE_HOST=localhost
NODE_RPC_PORT=8555

# Directorios
SNAPSHOTS_DIR=./snapshots
LOG_LEVEL=INFO
```

## Estructura del Proyecto

```
chia_prefarm_audit/
├── scripts/
│   ├── check_prefarm_balances.py  # Verificación de saldos
│   ├── monitor_transactions.py    # Monitoreo de transacciones
│   ├── address_utils.py          # Utilidades de direcciones
│   └── chia_db.py                # Clase para interactuar con la blockchain
├── snapshots/                    # Instantáneas de estados
├── logs/                         # Archivos de registro
├── .env                          # Variables de entorno
└── README.md                     # Este archivo
```

## Uso Avanzado

### Monitoreo Continuo con systemd (Linux)

Crea un servicio systemd para el monitoreo continuo:

```ini
# /etc/systemd/system/chia-prefarm-monitor.service
[Unit]
Description=Chia Prefarm Monitor
After=network.target

[Service]
User=usuario
WorkingDirectory=/ruta/a/chia_prefarm_audit
ExecStart=/usr/bin/python3 /ruta/a/chia_prefarm_audit/scripts/monitor_transactions.py
Restart=always
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
```

### Alertas por Correo Electrónico

Configura alertas por correo electrónico modificando el script `monitor_transactions.py`.

## Contribución

1. Haz un fork del repositorio
2. Crea una rama para tu característica (`git checkout -b feature/nueva-funcionalidad`)
3. Haz commit de tus cambios (`git commit -am 'Añadir nueva funcionalidad'`)
4. Haz push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Abre un Pull Request

## Licencia

Este proyecto está bajo la Licencia MIT.
