FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && \
    apt-get install -y snort tcpdump

# Prepara directory e file
RUN mkdir -p /etc/snort/rules /var/log/snort

COPY snort.conf /etc/snort/snort.conf
COPY rules/local.rules /etc/snort/rules/local.rules
COPY snort_start.sh /snort_start.sh

# Rendi eseguibile lo script
RUN chmod +x /snort_start.sh

ENTRYPOINT ["/snort_start.sh"]
