FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && \
    apt-get install -y snort

# Prepara directory e file
RUN mkdir -p /etc/snort/rules /var/log/snort

COPY snort.conf /etc/snort/snort.conf
COPY rules/local.rules /etc/snort/rules/local.rules

CMD ["snort","-A","console","-c","/etc/snort/snort.conf","-i","eth0"]
