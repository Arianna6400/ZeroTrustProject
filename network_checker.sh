#!/bin/bash

# Lista dei container da controllare
containers=(
  "zta_postgres"
  "zta_db_seeder"
  "zta_pep"
  "zta_pdp"
  "zta_iptables"
  "zta_squid"
  "zta_snort"
  "zta_splunk"
  "client_aziendale"
  "client_vpn"
  "client_domestica"
  "client_pubblica"
)

echo "=== Docker Network IP Verification ==="

for container in "${containers[@]}"; do
  echo -e "\n🔍 Controllando container: $container"

  if docker ps -q -f name="^${container}$" > /dev/null; then
    docker inspect -f '{{range .NetworkSettings.Networks}}{{.NetworkID}} {{.IPAddress}} {{end}}' "$container"
    
    echo "📡 Reti a cui è connesso:"
    docker inspect -f '{{json .NetworkSettings.Networks}}' "$container" | jq .

  else
    echo "⚠️ Container $container non in esecuzione o non trovato."
  fi
done
