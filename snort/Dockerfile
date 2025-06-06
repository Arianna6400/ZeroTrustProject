FROM patrickneise/snort

# Copia il file di configurazione di Snort
COPY snort.conf /etc/snort/snort.conf

# Modifica i permessi per permettere la lettura da parte di Snort
RUN chmod 644 /etc/snort/snort.conf && chown snort:snort /etc/snort/snort.conf

# Comando per avviare Snort
CMD ["/usr/sbin/snort", "-A", "console", "-c", "/etc/snort/snort.conf", "-i", "eth0"]
