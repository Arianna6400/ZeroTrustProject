#!/bin/bash
echo "[INFO] Avvio Snort su interfacce disponibili..."

mkdir -p /var/log/snort
chmod -R a+rwx /var/log/snort

# Avvia socat proxy su 8002 (ascolta come fosse il PEP)
socat TCP-LISTEN:8002,fork TCP:zta_pep:8002 &

for iface in eth0 eth1 eth2 eth3; do
    snort -A fast -c /etc/snort/snort.conf -i "$iface" -l /var/log/snort -K ascii >> /var/log/snort/snort_${iface}.log 2>&1 &
done

wait
