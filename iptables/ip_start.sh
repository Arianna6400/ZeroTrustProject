#!/bin/bash

echo "[ZTA-NAT] ✅ Abilito IP forwarding..."
sysctl -w net.ipv4.ip_forward=1

echo "[ZTA-NAT] 🔁 Pulizia e applicazione regole iptables complete..."

# Pulisce tutte le regole attuali
iptables -F INPUT
iptables -F OUTPUT
iptables -F FORWARD
iptables -t nat -F PREROUTING
iptables -t nat -F POSTROUTING

# === Sezione *filter ===

# Politiche di default
iptables -P INPUT DROP
iptables -P FORWARD ACCEPT
iptables -P OUTPUT ACCEPT

# Blocca ICMPv6
iptables -A INPUT -p ipv6-icmp -j DROP
iptables -A FORWARD -p ipv6-icmp -j DROP
iptables -A OUTPUT -p ipv6-icmp -j DROP

# Accesso di base
iptables -A INPUT -i lo -j ACCEPT
iptables -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT

# Protezione SYN flood
iptables -N DOS_FILTER
iptables -A DOS_FILTER -m limit --limit 50/second --limit-burst 100 -j RETURN
iptables -A DOS_FILTER -j DROP
iptables -A INPUT -p tcp --syn -j DOS_FILTER
iptables -A FORWARD -p tcp --syn -j DOS_FILTER

# ICMP rate limit
iptables -A INPUT -p icmp --icmp-type echo-request -m limit --limit 10/s --limit-burst 20 -j ACCEPT
iptables -A INPUT -p icmp --icmp-type echo-request -j DROP

# Accesso SSH
iptables -A INPUT -p tcp -s 10.10.1.0/24 --dport 22 -j ACCEPT
iptables -A INPUT -p tcp -s 10.10.2.0/24 --dport 22 -j ACCEPT
iptables -A INPUT -p tcp -s 10.10.3.0/24 --dport 22 -j ACCEPT
iptables -A INPUT -p tcp -s 10.10.4.0/24 --dport 22 -j DROP

# Accesso a PEP, PDP, Squid
iptables -A INPUT -p tcp -s 10.10.1.0/24 --dport 8002 -j ACCEPT
iptables -A INPUT -p tcp -s 10.10.2.0/24 --dport 8002 -j ACCEPT
iptables -A INPUT -p tcp -s 10.10.3.0/24 --dport 8002 -j ACCEPT
iptables -A INPUT -p tcp -s 10.10.4.0/24 --dport 8002 -j DROP

iptables -A INPUT -p tcp -s 10.10.1.0/24 --dport 8001 -j ACCEPT
iptables -A INPUT -p tcp --dport 8001 -j DROP

iptables -A INPUT -p tcp -s 10.10.1.0/24 --dport 3128 -j ACCEPT
iptables -A INPUT -p tcp -s 10.10.2.0/24 --dport 3128 -j ACCEPT
iptables -A INPUT -p tcp -s 10.10.3.0/24 --dport 3128 -j ACCEPT
iptables -A INPUT -p tcp --dport 3129 -j ACCEPT

iptables -A INPUT -p udp -s 10.10.1.0/24 --dport 8002 -j ACCEPT
iptables -A INPUT -p udp -s 10.10.2.0/24 --dport 8002 -j ACCEPT
iptables -A INPUT -p udp -s 10.10.3.0/24 --dport 8002 -j ACCEPT
iptables -A INPUT -p udp -s 10.10.4.0/24 --dport 8002 -j DROP

# FORWARD tra reti
iptables -A FORWARD -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT

iptables -A FORWARD -s 10.10.1.0/24 -d 10.10.4.0/24 -p tcp -m multiport --dports 80,443,21 -j ACCEPT
iptables -A FORWARD -s 10.10.1.0/24 -d 10.10.4.0/24 -p icmp --icmp-type echo-request -j ACCEPT
iptables -A FORWARD -s 10.10.2.0/24 -d 10.10.4.0/24 -p tcp -m multiport --dports 80,443,21 -j ACCEPT
iptables -A FORWARD -s 10.10.2.0/24 -d 10.10.4.0/24 -p icmp --icmp-type echo-request -j ACCEPT
iptables -A FORWARD -s 10.10.3.0/24 -d 10.10.4.0/24 -p tcp -m multiport --dports 80,443,21 -j ACCEPT
iptables -A FORWARD -s 10.10.3.0/24 -d 10.10.4.0/24 -p icmp --icmp-type echo-request -j ACCEPT
iptables -A FORWARD -s 10.10.4.0/24 -d 10.10.3.0/24 -p tcp --dport 5000 -j ACCEPT

# Da PEP a server
iptables -A FORWARD -s 10.10.3.222 -d 10.10.4.0/24 -p tcp -j ACCEPT
iptables -A FORWARD -s 10.10.3.222 -d 10.10.4.0/24 -p icmp --icmp-type echo-request -j ACCEPT
iptables -A FORWARD -s 10.10.3.222 -d 10.10.4.0/24 -p icmp --icmp-type echo-reply -j ACCEPT

iptables -A FORWARD -p udp --dport 8002 -j ACCEPT

# === Sezione *nat ===

# Proxy trasparente Squid
iptables -t nat -A PREROUTING -p tcp --dport 80 -j REDIRECT --to-port 3129
iptables -t nat -A PREROUTING -p tcp --dport 443 -j REDIRECT --to-port 3129

# MASQUERADE per rete pubblica
iptables -t nat -A POSTROUTING -s 10.10.5.0/24 -j MASQUERADE

# DNAT per PEP virtuale (zta_pep)
iptables -t nat -A PREROUTING -s 10.10.1.0/24 -d 10.10.255.254 -p tcp --dport 8002 -j DNAT --to-destination 10.10.1.222:8002
iptables -t nat -A PREROUTING -s 10.10.2.0/24 -d 10.10.255.254 -p tcp --dport 8002 -j DNAT --to-destination 10.10.1.222:8002
iptables -t nat -A PREROUTING -s 10.10.3.0/24 -d 10.10.255.254 -p tcp --dport 8002 -j DNAT --to-destination 10.10.1.222:8002
iptables -t nat -A PREROUTING -s 10.10.4.0/24 -d 10.10.255.254 -p tcp --dport 8002 -j DNAT --to-destination 10.10.1.222:8002

# === DNAT UDP per PEP virtuale ===
iptables -t nat -A PREROUTING -s 10.10.1.0/24 -d 10.10.255.254 -p udp --dport 8002 -j DNAT --to-destination 10.10.1.222:8002
iptables -t nat -A PREROUTING -s 10.10.2.0/24 -d 10.10.255.254 -p udp --dport 8002 -j DNAT --to-destination 10.10.1.222:8002
iptables -t nat -A PREROUTING -s 10.10.3.0/24 -d 10.10.255.254 -p udp --dport 8002 -j DNAT --to-destination 10.10.1.222:8002
iptables -t nat -A PREROUTING -s 10.10.4.0/24 -d 10.10.255.254 -p udp --dport 8002 -j DNAT --to-destination 10.10.1.222:8002

# Aggiungi IP virtuale a loopback se mancante
echo "[ZTA-NAT] 📡 Verifico IP virtuale 10.10.255.254 su lo..."
ip a | grep -q 10.10.255.254

echo "[ZTA-NAT] ✅ Tutte le regole iptables sono applicate."

tail -f /dev/null
