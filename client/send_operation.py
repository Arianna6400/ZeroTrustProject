import argparse
import requests
import os

parser = argparse.ArgumentParser(description="Client dinamico per PEP")
parser.add_argument("--operazione", required=True)
parser.add_argument("--risorsa", required=True)
parser.add_argument("--rete", default="aziendale")
parser.add_argument("--dispositivo", default="client-1")
parser.add_argument("--pep-url", default="http://zta_pep:8002/operazione")
args = parser.parse_args()

username = input("Username: ")
password = input("Password: ")

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

print("\nInvio richiesta al PEP...")
response = requests.post(args.pep_url, json=payload, headers=headers)
print("Status:", response.status_code)
print("Risposta:", response.json())