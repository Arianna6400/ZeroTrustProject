FROM ubuntu:20.04

ARG DEBIAN_FRONTEND=noninteractive

# Installa iptables, rsyslog e utilità base
RUN apt-get update && apt-get install -y iptables rsyslog procps

# Copia le regole iptables e lo script di avvio
COPY iptables.rules /iptables.rules
COPY ip_start.sh /ip_start.sh

# Rendi eseguibile lo script
RUN chmod +x /ip_start.sh

# Avvia il container usando lo script
ENTRYPOINT ["/ip_start.sh"]
