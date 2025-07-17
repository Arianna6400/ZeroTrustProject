#!/bin/bash
set -e

# Fix permessi su directory dei log condivisa con Postgres
if [ -d "/mnt/postgres_logs" ]; then
    echo "[INFO] Setting permissions on /mnt/postgres_logs"
    chmod -R a+rX /mnt/postgres_logs || true
    chmod -R a+rX /mnt/postgres_logs/postgresql.log || true
    echo "[INFO] Setted permissions on /mnt/postgres_logs"
fi

chown -R splunk:splunk /opt/splunk

# ✅ Avvia Splunk normalmente
exec /sbin/entrypoint.sh start