#!/bin/bash
set -e

echo "[INFO] Avvio Snort su interfacce Docker disponibili..."

mkdir -p /var/log/snort

for iface in $(ls /sys/class/net | grep -E '^eth|^en'); do
    echo "[INFO] Avvio su $iface"
    snort -A fast -c /etc/snort/snort.conf -i $iface -l /var/log/snort &
done

chmod -R a+rwx /var/log/snort

wait
