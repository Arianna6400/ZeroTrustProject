FROM ubuntu:20.04

# Impostazioni per evitare interazioni durante l'installazione dei pacchetti
ARG DEBIAN_FRONTEND=noninteractive

# Aggiorna e installa iptables, rsyslog e procps (per sysctl)
RUN apt-get update && apt-get install -y iptables rsyslog procps

# Copia le regole iptables e la configurazione rsyslog
COPY iptables.rules /iptables.rules
COPY rsyslog.conf /etc/rsyslog.conf

# Abilita logging netfilter nei namespace
RUN echo "net.netfilter.nf_log_all_netns=1" >> /etc/sysctl.conf

# Crea cartella log, script di avvio, e rendilo eseguibile
RUN mkdir -p /var/log/iptables_logs && \
    echo '#!/bin/bash' > /start.sh && \
    echo 'sysctl -w net.netfilter.nf_log_all_netns=1' >> /start.sh && \
    echo 'modprobe nf_log_ipv4 || true' >> /start.sh && \
    echo 'iptables-restore < /iptables.rules' >> /start.sh && \
    echo 'rsyslogd' >> /start.sh && \
    echo 'touch /var/log/iptables_logs/iptables.log' >> /start.sh && \
    echo 'tail -f /var/log/iptables_logs/iptables.log' >> /start.sh && \
    chmod +x /start.sh

# Avvio container
CMD ["/start.sh"]
