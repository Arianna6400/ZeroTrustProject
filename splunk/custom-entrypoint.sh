#!/bin/bash
set -e

# Fix permessi su directory dei log condivisa con Postgres
if [ -d "/mnt/postgres_logs" ]; then
    echo "[INFO] Setting permissions on /mnt/postgres_logs"
    chmod -R a+rX /mnt/postgres_logs || true
    chmod -R a+rX /mnt/postgres_logs/postgresql.log || true
    echo "[INFO] Setted permissions on /mnt/postgres_logs"
fi

if [ -d "/mnt/snort_logs" ]; then
    echo "[INFO] Setting permissions on /mnt/snort_logs"
    chmod -R a+rX /mnt/snort_logs || true
    chmod -R a+rX /mnt/snort_logs/*  || true
    echo "[INFO] Setted permissions on /mnt/snort_logs"
fi

# ✅ Avvia Splunk normalmente
exec /sbin/entrypoint.sh start