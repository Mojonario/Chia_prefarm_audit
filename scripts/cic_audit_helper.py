#!/usr/bin/env python3
"""
Helper functions to sync and audit a Chia prefarm singleton using the custody tool (cic).
"""

import subprocess
import sys
from pathlib import Path
import json
import csv
from datetime import datetime
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

def get_cic_executable():
    """Return full path to 'cic.exe' in venv, or 'cic' if not found."""
    project_root = Path(__file__).resolve().parent.parent
    cic_path = project_root / 'venv' / 'Scripts' / 'cic.exe'
    if cic_path.exists():
        return str(cic_path)
    return 'cic'


def audit_wallet(config_path: str, db_path: str, output_csv: str) -> str:
    """
    Syncs the prefarm configuration and audits it to produce a CSV.

    :param config_path: Path to the prefarm config .txt file.
    :param db_path: Path to the sqlite sync DB file.
    :param output_csv: Path to the output CSV file.
    :return: Path to the generated CSV.
    """
    cic = get_cic_executable()
    config = Path(config_path)
    db = Path(db_path)
    output = Path(output_csv)

    if not config.exists():
        raise FileNotFoundError(f"Config file not found: {config}")
    # Ensure directories exist
    db.parent.mkdir(parents=True, exist_ok=True)
    output.parent.mkdir(parents=True, exist_ok=True)

    # Run sync
    logger.info(" cic sync with config=%s db=%s", config, db)
    subprocess.run([cic, 'sync', '-c', str(config), '-db', str(db)], check=True)
    logger.info(" cic sync completed")
    # Run audit
    logger.info(" cic audit output=%s", output)
    subprocess.run([cic, 'audit', '-db', str(db), '-f', str(output)], check=True)
    logger.info(" cic audit completed, CSV generated at %s", output)

    return str(output)


def extract_json_objects(text):
    """Extrae objetos JSON de un texto que puede contener múltiples objetos."""
    decoder = json.JSONDecoder()
    pos = 0
    while pos < len(text):
        match = text.find('{', pos)
        if match == -1:
            break
        try:
            obj, idx = decoder.raw_decode(text[match:])
            yield obj
            pos = match + idx
        except json.JSONDecodeError:
            pos = match + 1


def process_audit_csv(input_csv_path: str, output_csv_path: str):
    """Procesa el CSV de auditoría para extraer fecha y cantidad XCH."""
    input_path = Path(input_csv_path)
    output_path = Path(output_csv_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    text = input_path.read_text(encoding='utf-8')
    # Count JSON objects
    total_json = sum(1 for _ in extract_json_objects(text))
    logger.info(" Parsed %d JSON objects from audit CSV", total_json)
    transactions = []
    for obj in extract_json_objects(text):
        if isinstance(obj, dict) and obj.get('action') == 'HANDLE_PAYMENT':
            try:
                timestamp = obj['time']
                date = datetime.utcfromtimestamp(timestamp).strftime('%Y-%m-%d')
                amount_mojos = int(obj['params']['out_amount'])
                amount_xch = amount_mojos / 10**12
                transactions.append({'timestamp': timestamp, 'date': date, 'amount_xch': amount_xch})
            except (KeyError, ValueError):
                continue
    if not transactions:
        logger.error("No HANDLE_PAYMENT transactions found in %s", input_path)
        raise ValueError("No se encontraron transacciones HANDLE_PAYMENT.")
    logger.info(" Found %d HANDLE_PAYMENT transactions", len(transactions))
    transactions.sort(key=lambda x: x['timestamp'])
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['time', 'amount_xch'])
        writer.writeheader()
        for tx in transactions:
            writer.writerow({'time': tx['date'], 'amount_xch': f"{tx['amount_xch']:.12f}"})


def audit_and_process_wallet(config_path: str, db_path: str, audit_csv: str, summary_csv: str) -> str:
    """Sincroniza, audita y procesa el CSV de la wallet."""
    csv_path = audit_wallet(config_path, db_path, audit_csv)
    process_audit_csv(csv_path, summary_csv)
    return summary_csv


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description="Sync and audit a Chia prefarm singleton.")
    parser.add_argument('-c', '--config', required=True, help="Path to prefarm config .txt file")
    parser.add_argument('-db', '--db', required=True, help="Path to sqlite sync DB file")
    parser.add_argument('-f', '--file', required=True, help="Path to output CSV file")
    parser.add_argument('-s', '--summary', required=True, help="Path to summary CSV file")
    args = parser.parse_args()
    try:
        result = audit_and_process_wallet(args.config, args.db, args.file, args.summary)
        logger.info("Audit written to %s", result)
        sys.exit(0)
    except subprocess.CalledProcessError as e:
        logger.error("cic command failed: %s", e)
        sys.exit(e.returncode)
    except Exception as e:
        logger.error("Error during audit processing: %s", e)
        sys.exit(1)
