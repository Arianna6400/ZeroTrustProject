FROM splunk/splunk:latest

USER root

RUN rm -f /opt/splunk/etc/auth/cacert.pem

COPY ./inputs.conf /opt/splunk/etc/system/local/inputs.conf
COPY ./props.conf /opt/splunk/etc/system/local/props.conf
COPY ./indexes.conf /opt/splunk/etc/system/local/indexes.conf

COPY custom-entrypoint.sh /custom-entrypoint.sh
RUN chmod +x /custom-entrypoint.sh

ENTRYPOINT ["/custom-entrypoint.sh"]