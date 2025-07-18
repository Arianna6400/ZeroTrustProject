import hashlib
from flask import Flask, request, jsonify
import requests
import os
import psycopg2
import logging
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

PEP_PORT = int(os.getenv('PEP_PORT'))
PDP_VALUTA = os.getenv('PDP_VALUTA')

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

# Politiche scritte direttamente nel codice
POLICIES = [
    {
        "nome": "Accesso dati sanitari Medico",
        "descrizione": "Solo Medico o Amministratore possono accedere a dati sanitari",
        "risorsa": "sensibile",
        "operazione": "scrittura",
        "ruoli_ammessi": ["Amministratore", "Personale"],
        "rete_richiesta": None,
        "soglia": 0.7
    },
    {
        "nome": "Accesso tramite dispositivi personali autorizzati",
        "descrizione": "Accesso ai dati sanitari consentito anche da dispositivi personali",
        "risorsa": "sensibile",
        "operazione": "scrittura",
        "ruoli_ammessi": ["Personale", "Amministratore"],
        "rete_richiesta": None,
        "soglia": 0.5
    },
    {
        "nome": "Accesso in caso di emergenza",
        "descrizione": "Accesso urgente in caso di emergenza sanitaria fuori orario",
        "risorsa": "urgente",
        "operazione": "lettura",
        "ruoli_ammessi": ["Personale", "Amministratore"],
        "rete_richiesta": None,
        "soglia": 0.65
    },
    {
        "nome": "Accesso dati sanitari Personale sanitario",
        "descrizione": "Solo personale sanitario in rete aziendale può accedere a dati sensibili",
        "risorsa": "sensibile",
        "operazione": "scrittura",
        "ruoli_ammessi": ["Personale"],
        "rete_richiesta": "aziendale",
        "soglia": 0.6
    },
    {
        "nome": "Dispositivi compromessi o non protetti",
        "descrizione": "Accesso negato da dispositivi compromessi",
        "risorsa": "informativi",
        "operazione": "restrizioni",
        "ruoli_ammessi": ["Personale", "Amministratore", "Guest"],
        "rete_richiesta": None,
        "soglia": 0.6
    }
]

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

    rete = request.headers.get("X-Rete", "sconosciuta").lower()
    dispositivo = request.headers.get("X-Dispositivo", "sconosciuto")

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
        fiducia = risposta.json().get("fiducia", 0)
    except Exception as e:
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