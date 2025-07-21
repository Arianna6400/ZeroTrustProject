import argparse
import requests
import getpass
import json
import os

# Carica config.json nella stessa directory dello script
CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")

def load_config(path):
    try:
        with open(path, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"⚠️ Errore nel caricamento di {path}: {e}")
        return {}

config = load_config(CONFIG_PATH)

parser = argparse.ArgumentParser(description="Client dinamico per PEP")
parser.add_argument("--username", help="Nome utente (interattivo se assente)")
parser.add_argument("--password", help="Password (interattivo se assente)")
parser.add_argument("--operazione", required=True, help="Operazione (es: lettura, scrittura)")
parser.add_argument("--risorsa", required=True, help="Risorsa da accedere (es: Cartella Clinica)")
parser.add_argument("--rete", default="aziendale", help="Tipo di rete")
parser.add_argument("--dispositivo", default="aziendale", help="Tipo di dispositivo")
parser.add_argument("--pep-url", help="Override URL del PEP")
args = parser.parse_args()

username = args.username or input("Username: ")
password = args.password or getpass.getpass("Password: ")

pep_url = args.pep_url or config.get("pep_url")
proxy_url = config.get("proxy_url")

if not pep_url:
    raise RuntimeError("❌ URL del PEP non specificato né in CLI né in config.json")

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

proxies = {"http": proxy_url} if proxy_url else {}

print("\n🚀 Invio richiesta al PEP...")
try:
    response = requests.post(
        pep_url,
        json=payload,
        headers=headers,
        proxies=proxies
    )
    print("✅ Status:", response.status_code)
    try:
        risposta_json = response.json()
        print("📦 Risposta:")
        print(json.dumps(risposta_json, indent=2, ensure_ascii=False))
    except ValueError:
        print("⚠️ La risposta non è in formato JSON:")
        print(response.text)

except requests.exceptions.RequestException as e:
    print("❌ Errore nella richiesta:", str(e))
