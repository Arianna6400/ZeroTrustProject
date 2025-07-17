#!/bin/bash
set -e

# Fix permessi sulle directory dei log
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

if [ -d "/mnt/squid_logs" ]; then
    echo "[INFO] Setting permissions on /mnt/squid_logs"
    chmod -R a+rX /mnt/squid_logs || true
    chmod -R a+rX /mnt/squid_logs/access.log || true
    echo "[INFO] Setted permissions on /mnt/squid_logs"
fi

# ✅ Avvia Splunk normalmente
exec /sbin/entrypoint.sh start