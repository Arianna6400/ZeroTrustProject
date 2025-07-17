from flask import Flask, request, jsonify
import os
import requests as req
import logging
import json
from dotenv import load_dotenv

load_dotenv()

def must_get_env(name):
    value = os.getenv(name)
    if value is None:
        raise EnvironmentError(f"Variabile d'ambiente obbligatoria '{name}' mancante.")
    return value

def setup_logger():
    LOG_DIR = must_get_env("LOG_DIR")
    LOG_FILE = must_get_env("LOG_FILE")
    full_path = os.path.join(LOG_DIR, LOG_FILE)

    os.makedirs(LOG_DIR, exist_ok=True)

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Evita di aggiungere handler multipli se già presenti
    if not logger.hasHandlers():
        # File handler
        fh = logging.FileHandler(full_path)
        fh.setLevel(logging.INFO)
        fh.setFormatter(logging.Formatter('[%(asctime)s] %(levelname)s - %(message)s'))
        logger.addHandler(fh)

        # Console handler
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        logger.addHandler(ch)

SPLUNK_HOST = must_get_env("SPLUNK_HOST")
SPLUNK_USERNAME = must_get_env("SPLUNK_USERNAME")
SPLUNK_PASSWORD = must_get_env("SPLUNK_PASSWORD")
PDP_PORT    = int(must_get_env("PDP_PORT"))

app = Flask(__name__)

setup_logger()

BASE_TRUST = {
    "amministratore": 0.6,
    "personale": 0.4,
    "guest": 0.2,
    "sconosciuto": 0.1,
}

NETWORK_TRUST = {
    "network_aziendale": 0.3,
    "network_vpn": 0.15,
    "network_domestica": 0.05,
    "network_pubblica": -0.05
}

DEVICE_TRUST = {
    "aziendale": 0.08,
    "privato": 0.04,
}

PENALTY_SENSITIVE = 0.1
PENALTY_WRITE = 0.13

def splunk_search(index, term, limit=10, earliest_time=None):
    
    if not SPLUNK_USERNAME or not SPLUNK_PASSWORD:
        logging.warning("Splunk credentials missing! Returning no results.")
        return []
    
    time_filter = f' earliest="{earliest_time}" latest="now"' if earliest_time else ""
    query = f'search index={index} {term}{time_filter} | head {limit}'
    try:
        job = req.post(
            f"{SPLUNK_HOST}/services/search/jobs",
            data={"search": query, "output_mode":"json"},
            auth=(SPLUNK_USERNAME, SPLUNK_PASSWORD),
            verify=False, timeout=15
        )
        job.raise_for_status()
        sid = job.json().get("sid")
        if not sid:
            return []
        
        for _ in range(15):
            r = req.get(
                f"{SPLUNK_HOST}/services/search/jobs/{sid}",
                params={"output_mode": "json"},
                auth=(SPLUNK_USERNAME, SPLUNK_PASSWORD),
                verify=False, timeout=5
            )
            r.raise_for_status()
            if r.json()["entry"][0]["content"]["isDone"]:
                break
        
        res = req.get(
            f"{SPLUNK_HOST}/services/search/jobs/{sid}/results",
            params={"output_mode": "json"},
            auth=(SPLUNK_USERNAME, SPLUNK_PASSWORD),
            verify=False, timeout=10
        )
        res.raise_for_status()
        return res.json().get("results", [])
    except Exception as e:
        logging.error(f"Splunk search failed: {e}")
        return []
    
def calculate_trust(context):
    ruolo = context.get("soggetto", "")
    rete = context.get("rete", "")
    dispositivo = context.get("dispositivo", "")
    
    trust = BASE_TRUST.get(ruolo, 0.1)
    trust += NETWORK_TRUST.get(rete, 0)
    trust += DEVICE_TRUST.get(dispositivo, 0)    
    
    squid_logs = splunk_search("squid", context.get("rete", ""), 10, earliest_time="-2m")
    for log in squid_logs:
        raw = log.get("_raw", "")
        if "TCP_DENIED/403" in raw:
            trust -= 0.1
            logging.info(f"Accesso negato su squid log -> penalità -0.1")
    
    snort_logs = splunk_search("snort", context.get("rete", ""), 10, earliest_time="-2m")
    for log in snort_logs:
        raw = log.get("_raw", "")
        if "[Priority: 1]" in raw:
            trust -= 0.15
            logging.info(f"Snort alert Priority 1 -> penalità -0.15")
        elif "[Priority: 2]" in raw:
            trust -= 0.07
            
    trust = max(0, min(1, trust))
    return trust

@app.route("/valuta", methods=["POST"])
def valuta():
    context = request.get_json()
    trust = calculate_trust(context)
    logging.info(f"PDP: Valutazione per {context}: trust={trust}")
    return jsonify({"fiducia": trust})

if __name__ == '__main__':
    logging.info(f"PDP avviato: il servizio è in ascolto sulla porta {PDP_PORT}")
    app.run(host='0.0.0.0', port=PDP_PORT, debug=False)
