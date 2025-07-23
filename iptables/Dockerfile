FROM ubuntu:20.04

ARG DEBIAN_FRONTEND=noninteractive

# Installa iptables e tool necessari
RUN apt-get update && \
    apt-get install -y iptables iproute2 procps && \
    apt-get clean

# Copia lo script completo con tutte le regole iptables
COPY ip_start.sh /ip_start.sh

# Rendi eseguibile lo script
RUN chmod +x /ip_start.sh

# Esegui lo script all'avvio
ENTRYPOINT ["/ip_start.sh"]
