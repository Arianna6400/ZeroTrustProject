#!/bin/bash

# Abilita IP forwarding
sysctl -w net.ipv4.ip_forward=1

# Flush delle regole precedenti
iptables -F
iptables -X
iptables -t nat -F

# Applica le regole iptables
iptables-restore < /iptables.rules

# Tieni vivo il container
echo "[IPTABLES] Regole applicate. Container attivo."
sleep infinity
