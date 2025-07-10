FROM ubuntu:20.04

# Impostazioni per evitare interazioni durante l'installazione dei pacchetti
ARG DEBIAN_FRONTEND=noninteractive

# Aggiorna l'immagine e installa iptables
RUN apt-get update && apt-get install -y iptables rsyslog

# Aggiungi il file di regole iptables all'interno del container
COPY iptables.rules /iptables.rules
COPY rsyslog.conf /etc/rsyslog.conf

# Aggiungi uno script di avvio che ripristina le regole di iptables all'avvio
RUN echo "#!/bin/bash\n\
service rsyslog start\n\
iptables-restore < /iptables.rules\n\
touch /var/log/iptables_logs/iptables.log\n\
tail -f /var/log/iptables_logs/iptables.log" > /start.sh && chmod +x /start.sh

# Impostiamo il comando di avvio come lo script di avvio
CMD ["/start.sh"]