
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

# 🔑 Funzione per hash della password (esempio base)
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Funzione di esempio per determinare la soglia minima richiesta
def get_threshold(operazione, risorsa):
    if risorsa == "sensibile":
        return 0.8 if operazione == "scrittura" else 0.6
    else:
        return 0.5 if operazione == "scrittura" else 0.1

@app.route('/operazione', methods=['POST'])
def gestisci_operazione():
    dati = request.get_json()

    # 1. Estrai dati dal body
    username = dati.get("username")
    password = dati.get("password")  # eventualmente usato per autenticazione futura
    operazione = dati.get("operazione")
    risorsa = dati.get("risorsa")

    # 2. Estrai header impostati da Squid
    rete = request.headers.get("X-Rete", "sconosciuta")
    dispositivo = request.headers.get("X-Dispositivo", "sconosciuto")

    if not all([username, password, operazione, risorsa]):
        return jsonify({"errore": "Dati incompleti"}), 400
    
    password_hash = hash_password(password)

    # 🔍 Recupera ruolo dell'utente
    cur.execute(
        "SELECT user_role FROM users WHERE username = %s AND password_hash = %s",
        (username, password_hash)
    )
    user_row = cur.fetchone()
    if not user_row:
        return jsonify({"errore": "Credenziali non valide",
                        "username": username,
                        "has_password": password_hash
                        }), 401
    
    soggetto = user_row[0]

    # 🔍 Recupera tipo della risorsa
    cur.execute(
        "SELECT tipo_risorsa FROM tipi_risorse WHERE nome = %s",
        (risorsa,)
    )
    risorsa_row = cur.fetchone()
    if not risorsa_row:
        return jsonify({"errore": "Risorsa non trovata"}), 404

    tipo_risorsa = risorsa_row[0]

    #risorsa = 

    # 3. Costruisci il contesto per il PDP
    contesto = {
        "soggetto": soggetto,
        "rete": rete,
        "dispositivo": dispositivo,
        "operazione": operazione,
        "risorsa": tipo_risorsa
    }

    # 4. Chiedi valutazione al PDP
    try:
        risposta = requests.post(PDP_VALUTA, json=contesto)
        risposta.raise_for_status()
        fiducia = risposta.json().get("fiducia", 0)
    except Exception as e:
        return jsonify({"errore": f"Errore nella valutazione PDP: {str(e)}"}), 500

    # 5. Valuta contro soglia
    soglia = get_threshold(operazione, risorsa)
    if fiducia >= soglia:
        # Esegui l'azione autorizzata sul DB (placeholder)
        return jsonify({"accesso": "concesso", 
                        "livello_fiducia": fiducia,
                        "soggetto": soggetto,
                        "rete": rete,
                        "dispositivo": dispositivo,
                        "operazione": operazione,
                        "risorsa": tipo_risorsa
                        }), 200
    else:
        return jsonify({"accesso": "negato", 
                        "livello_fiducia": fiducia,
                        "soggetto": soggetto,
                        "rete": rete,
                        "dispositivo": dispositivo,
                        "operazione": operazione,
                        "risorsa": tipo_risorsa
                        }), 403

if __name__ == '__main__':
    logging.info(f"PEP avviato: il servizio è in ascolto sulla porta {PEP_PORT}")
    app.run(host='0.0.0.0', port=PEP_PORT)
