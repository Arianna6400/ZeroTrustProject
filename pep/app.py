import hashlib
from flask import Flask, request, jsonify
import requests
import os
import psycopg2
import logging
import json
import socket
from dotenv import load_dotenv

# Risoluzione dinamica di zta_pep
def configura_hosts_dinamico():
    try:
        ip_locale = socket.gethostbyname(socket.gethostname())
        rete_id = ip_locale.split('.')[2]
        ip_pep = f"10.10.{rete_id}.222"

        print(f"[ZTA-PEP] ➕ Configuro /etc/hosts: zta_pep → {ip_pep}")
        with open("/etc/hosts", "a") as hosts_file:
            hosts_file.write(f"{ip_pep} zta_pep\n")

    except Exception as e:
        print(f"[ZTA-PEP] ⚠️ Errore nella configurazione dinamica di /etc/hosts: {e}")

load_dotenv()
configura_hosts_dinamico()

app = Flask(__name__)

PEP_PORT = int(os.getenv('PEP_PORT'))
PDP_VALUTA = os.getenv('PDP_VALUTA')
POLICY_FILE = os.getenv('POLICY_FILE', 'policies.json')

# 📁 Configura logging su file
LOG_FILE = '/mnt/pep_logs/pep.log'
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)

try:
    conn = psycopg2.connect(
        host=os.environ['DB_HOST'],
        port=os.environ['DB_PORT'],
        dbname=os.environ['DB_NAME'],
        user=os.environ['DB_USER'],
        password=os.environ['DB_PASSWORD']
    )
    cur = conn.cursor()
    logging.info("Connessione al database riuscita.")
except Exception as db_err:
    logging.error(f"Errore nella connessione al database: {db_err}")
    raise db_err

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
def trova_policy(context, policies):
    ruolo = context.get("soggetto")
    risorsa = context.get("risorsa")
    operazione = context.get("operazione")
    rete = context.get("rete")
    dispositivo = context.get("dispositivo")

    candidate_policies = []
    for policy in policies:
        if not all(k in policy for k in ["risorsa", "operazione", "ruoli_ammessi"]):
            logging.warning(f"Policy incompleta ignorata: {policy}")
            continue
        if policy.get("risorsa") != risorsa or policy.get("operazione") != operazione:
            continue
        if ruolo not in policy.get("ruoli_ammessi", []):
            continue
        if policy.get("rete_richiesta") is not None and rete not in policy.get("rete_richiesta", []):
            continue
        if policy.get("dispositivo_richiesto") is not None and dispositivo not in policy.get("dispositivo_richiesto", []):
            continue
        candidate_policies.append(policy)

    if not candidate_policies:
        logging.warning(f"Nessuna policy applicabile trovata per il contesto: {context}")
        return None

    # Se più policy sono valide, scegli quella con la soglia più alta
    selected = max(candidate_policies, key=lambda p: p["soglia"])
    logging.info(f"Policy selezionata: {selected['nome']} con soglia {selected['soglia']}")
    return selected

@app.route('/operazione', methods=['POST'])
def gestisci_operazione():
    dati = request.get_json()
    logging.info(f"Richiesta ricevuta: {dati}")

    username = dati.get("username")
    password = dati.get("password")
    operazione = dati.get("operazione")
    risorsa = dati.get("risorsa")

    rete_header = request.headers.get("X-Rete", "sconosciuta").lower()
    rete = rete_header.split(',')[0].strip()

    ip_client = request.headers.get("X-IP", request.remote_addr)

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
        logging.warning(f"Login fallito per utente '{username}' da IP {ip_client}")
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
        "risorsa": tipo_risorsa,
        "ip_client": ip_client,
        "username": username
    }

    policy = trova_policy(contesto, POLICIES)

    if policy:
        soglia = policy['soglia']
    else:
        logging.info(f"Accesso negato - Nessuna policy applicabile per il contesto")
        return jsonify({
            "esito": "negato",
            "motivazione": "Nessuna policy applicabile per il contesto richiesto"
        }), 403

    try:
        risposta = requests.post(PDP_VALUTA, json=contesto)
        risposta.raise_for_status()
        try:
            fiducia = risposta.json().get("fiducia", 0)
        except Exception as json_err:
            return jsonify({"errore": f"PDP ha risposto ma non in formato JSON: {str(json_err)}"}), 500
    except requests.exceptions.RequestException as e:
        return jsonify({"errore": f"Errore nella valutazione PDP: {str(e)}"}), 500
    
    logging.info(f"Risposta PDP: fiducia={fiducia:.2f}, soglia={soglia:.2f}")

    accesso = "concesso" if fiducia >= soglia else "negato"

    risultato = {
    "accesso": accesso,
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

    logging.info(
    f"Utente: {username} | IP: {ip_client} | Operazione: {operazione} su risorsa: {risorsa} | "
    f"Ruolo: {soggetto} | Accesso: {accesso} (fiducia={fiducia:.2f}, soglia={soglia:.2f})"
)

    return jsonify(risultato), 200 if accesso == "concesso" else 403


if __name__ == '__main__':
    logging.info(f"PEP avviato: il servizio è in ascolto sulla porta {PEP_PORT}")
    app.run(host='0.0.0.0', port=PEP_PORT)