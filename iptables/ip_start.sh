#!/bin/bash

# Applica le regole iptables
iptables-restore < /iptables.rules

# Tieni vivo il container
echo "[IPTABLES] Regole applicate. Container attivo."
sleep infinity
