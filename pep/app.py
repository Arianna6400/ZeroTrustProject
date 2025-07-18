import hashlib
from flask import Flask, request, jsonify
import requests
import os
import psycopg2
import logging
import json
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

PEP_PORT = int(os.getenv('PEP_PORT'))
PDP_VALUTA = os.getenv('PDP_VALUTA')
POLICY_FILE = os.getenv('POLICY_FILE', 'policies.json')

# 🔐 Connessione al database
conn = psycopg2.connect(
    host=os.environ['DB_HOST'],
    port=os.environ['DB_PORT'],
    dbname=os.environ['DB_NAME'],
    user=os.environ['DB_USER'],
    password=os.environ['DB_PASSWORD']
)
cur = conn.cursor()

# 🔑 Funzione per hash della password

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# 📄 Carica policy da file JSON
def carica_policy_da_file(percorso):
    try:
        with open(percorso, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Errore nel caricamento delle policy: {e}")
        return []

POLICIES = carica_policy_da_file(POLICY_FILE)

# Trova policy che si applica al contesto
def trova_policy(tipo_risorsa, operazione):
    for policy in POLICIES:
        if policy['risorsa'] == tipo_risorsa and policy['operazione'].lower() == operazione.lower():
            return policy
    return None

@app.route('/operazione', methods=['POST'])
def gestisci_operazione():
    dati = request.get_json()

    username = dati.get("username")
    password = dati.get("password")
    operazione = dati.get("operazione")
    risorsa = dati.get("risorsa")

    rete_header = request.headers.get("X-Rete", "sconosciuta").lower()
    rete = rete_header.split(',')[0].strip()

    dispositivo_header = request.headers.get("X-Dispositivo", "sconosciuto")
    dispositivo = dispositivo_header.split(',')[0].strip()

    if not all([username, password, operazione, risorsa]):
        return jsonify({"errore": "Dati incompleti"}), 400

    password_hash = hash_password(password)

    cur.execute(
        "SELECT user_role FROM users WHERE username = %s AND password_hash = %s",
        (username, password_hash)
    )
    user_row = cur.fetchone()
    if not user_row:
        return jsonify({"errore": "Credenziali non valide"}), 401

    soggetto = user_row[0]

    cur.execute(
        "SELECT tipo_risorsa FROM tipi_risorse WHERE nome = %s",
        (risorsa,)
    )
    risorsa_row = cur.fetchone()
    if not risorsa_row:
        return jsonify({"errore": "Risorsa non trovata"}), 404

    tipo_risorsa = risorsa_row[0]

    contesto = {
        "soggetto": soggetto,
        "rete": rete,
        "dispositivo": dispositivo,
        "operazione": operazione,
        "risorsa": tipo_risorsa
    }

    policy = trova_policy(tipo_risorsa, operazione)

    if policy:
        if soggetto not in policy['ruoli_ammessi']:
            return jsonify({"accesso": "negato", "motivo": "Ruolo non autorizzato per questa operazione"}), 403
        if policy['rete_richiesta'] and rete != policy['rete_richiesta']:
            return jsonify({"accesso": "negato", "motivo": "Rete non autorizzata per questa operazione"}), 403
        soglia = policy['soglia']
    else:
        if tipo_risorsa == "sensibile":
            soglia = 0.8 if operazione.lower() == "scrittura" else 0.6
        else:
            soglia = 0.5 if operazione.lower() == "scrittura" else 0.1

    try:
        risposta = requests.post(PDP_VALUTA, json=contesto)
        risposta.raise_for_status()
        try:
            fiducia = risposta.json().get("fiducia", 0)
        except Exception as json_err:
            return jsonify({"errore": f"PDP ha risposto ma non in formato JSON: {str(json_err)}"}), 500
    except requests.exceptions.RequestException as e:
        return jsonify({"errore": f"Errore nella valutazione PDP: {str(e)}"}), 500

    risultato = {
    "accesso": "concesso" if fiducia >= soglia else "negato",
    "soggetto": soggetto,
    "operazione": operazione,
    "risorsa": tipo_risorsa,
    "rete": rete,
    "dispositivo": dispositivo,
    
    "dettagli_policy": {
        "policy_applicata": policy['nome'] if policy else "Default dinamica",
        "soglia": round(soglia, 2),
        "livello_fiducia": round(fiducia, 2)
        }
    }


    return jsonify(risultato), 200 if fiducia >= soglia else 403


if __name__ == '__main__':
    logging.info(f"PEP avviato: il servizio è in ascolto sulla porta {PEP_PORT}")
    app.run(host='0.0.0.0', port=PEP_PORT)