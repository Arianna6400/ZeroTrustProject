import argparse
import requests
import os
import getpass

# docker exec -it client_interattivo python3 /app/send_operation.py   --operazione lettura   --risorsa "Orario di visita"

# Argomenti da riga di comando
parser = argparse.ArgumentParser(description="Client dinamico per PEP")
parser.add_argument("--username", help="Nome utente (interattivo se assente)")
parser.add_argument("--password", help="Password (interattivo se assente)")
parser.add_argument("--operazione", required=True, help="Operazione da eseguire (es: lettura, scrittura)")
parser.add_argument("--risorsa", required=True, help="Risorsa da accedere (match con tipi_risorse.nome)")
parser.add_argument("--rete", default="aziendale", help="Tipo di rete")
parser.add_argument("--dispositivo", default="aziendale", help="Tipo del dispositivo")
parser.add_argument("--pep-url", default="http://zta_pep:8002/operazione", help="Endpoint del PEP")
args = parser.parse_args()

# Prompt interattivo se non forniti
username = args.username or input("Username: ")
password = args.password or getpass.getpass("Password: ")  # ← sicuro

# Payload della richiesta
payload = {
    "username": username,
    "password": password,
    "operazione": args.operazione,
    "risorsa": args.risorsa
}

headers = {
    "X-Rete": args.rete,
    "X-Dispositivo": args.dispositivo
}

# 🚀 Invio della richiesta
print("\nInvio richiesta al PEP...")
try:
    response = requests.post(args.pep_url, json=payload, headers=headers)
    print("✅ Status:", response.status_code)
    print("📩 Risposta:", response.json())
except Exception as e:
    print("❌ Errore nella richiesta:", str(e))
