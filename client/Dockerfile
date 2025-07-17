FROM python:3.10-slim

WORKDIR /app

COPY send_operation.py .

# Installa i tool di rete necessari
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        iputils-ping \
        curl \
        netcat-traditional \
        ca-certificates \
        iproute2 && \
    pip install requests && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

CMD ["sleep", "infinity"]
