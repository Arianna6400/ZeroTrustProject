FROM ubuntu:20.04

# Impostazioni per evitare interazioni durante l'installazione dei pacchetti
ARG DEBIAN_FRONTEND=noninteractive

# Aggiorna l'immagine e installa iptables
RUN apt-get update && apt-get install -y iptables

# Aggiungi il file di regole iptables all'interno del container
COPY iptables.rules /iptables.rules

# Aggiungi uno script di avvio che ripristina le regole di iptables all'avvio
RUN echo "#!/bin/bash\n\
iptables-restore < /iptables.rules\n\
tail -f /dev/null" > /start.sh && chmod +x /start.sh

# Impostiamo il comando di avvio come lo script di avvio
CMD ["/start.sh"]