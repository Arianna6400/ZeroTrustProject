#!/bin/bash
echo "[INFO] Avvio Snort su interfacce disponibili..."

mkdir -p /var/log/snort
chmod -R a+rwx /var/log/snort

for iface in $(ls /sys/class/net); do
    LOGFILE="/var/log/snort/snort_${iface}.log"

    if [[ "$iface" == "lo" ]]; then
        echo "[INFO] Avvio Snort su interfaccia loopback ($iface) IN FOREGROUND per log visibile"
        snort -A fast -c /etc/snort/snort.conf -i "$iface" -l /var/log/snort -K ascii
    else
        echo "[INFO] Avvio Snort su interfaccia $iface in background. Log: $LOGFILE"
        snort -A fast -c /etc/snort/snort.conf -i "$iface" -l /var/log/snort -K ascii >> "$LOGFILE" 2>&1 &
    fi
done

wait
