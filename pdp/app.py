from flask import Flask, request, jsonify
import os
import requests as req
import logging
import json
from dotenv import load_dotenv
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

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

    if not logger.hasHandlers():
        fh = logging.FileHandler(full_path)
        fh.setLevel(logging.INFO)
        fh.setFormatter(logging.Formatter('[%(asctime)s] %(levelname)s - %(message)s'))
        logger.addHandler(fh)

        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        logger.addHandler(ch)

SPLUNK_HOST = must_get_env("SPLUNK_HOST")
SPLUNK_USERNAME = must_get_env("SPLUNK_USERNAME")
SPLUNK_PASSWORD = must_get_env("SPLUNK_PASSWORD")
PDP_PORT = int(must_get_env("PDP_PORT"))

app = Flask(__name__)

setup_logger()

# PESI (devono sommare a 1.0)
WEIGHTS = {
    "ruolo": 0.25,
    "rete": 0.15,
    "dispositivo": 0.10,
    "squid": 0.15,
    "snort": 0.20,
    "pep": 0.15
}

# Punteggio base ruolo: già da 0 a 1
BASE_TRUST = {
    "amministratore": 1.0,
    "personale": 0.7,
    "guest": 0.4,
    "sconosciuto": 0.2,
}

NETWORK_SCORE = {
    "aziendale": 1.0,
    "vpn": 0.8,
    "domestica": 0.5,
    "pubblica": 0.3
}

DEVICE_SCORE = {
    "aziendale": 1.0,
    "privato": 0.6
}

PENALTY_SQUID = 0.1
BONUS_SQUID = 0.02
PENALTY_SNORT_1 = 0.2
PENALTY_SNORT_2 = 0.1
PENALTY_PEP_FAIL_IP = 0.05
PENALTY_PEP_FAIL_USER = 0.03
BONUS_PEP = 0.01

TRUST_CAP = 1.0
TRUST_FLOOR = 0.0

def splunk_search(index, term, limit=10, earliest_time=None):
    if not SPLUNK_USERNAME or not SPLUNK_PASSWORD:
        logging.warning("Splunk credentials missing! Returning no results.")
        return []

    time_filter = f' earliest="{earliest_time}" latest="now"' if earliest_time else ""
    query = f'search index={index} {term}{time_filter} | head {limit}'
    try:
        job = req.post(
            f"{SPLUNK_HOST}/services/search/jobs",
            data={"search": query, "output_mode": "json"},
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

def score_squid(logs):
    penalty_codes = ["TCP_DENIED", "TCP_RESET", "TCP_HIT/403", "TCP_MISS/403", "TCP_DENIED/403"]
    bonus_codes = ["TCP_HIT/200", "TCP_MISS/200", "TCP_REFRESH_HIT", "TCP_IMS_HIT"]

    denied_count = 0
    success_count = 0

    for log in logs:
        raw = log.get("_raw", "")
        if any(code in raw for code in penalty_codes):
            denied_count += 1
        elif any(code in raw for code in bonus_codes):
            success_count += 1

    score = 1 - (PENALTY_SQUID * denied_count) + (BONUS_SQUID * success_count)
    score = min(max(score, 0.0), 1.0)

    logging.info(f"Squid score = {score:.2f} (deny={denied_count}, success={success_count})")
    return score

def score_snort(logs):

    p1 = sum(1 for log in logs if "[Priority: 1]" in log.get("_raw", ""))
    p2 = sum(1 for log in logs if "[Priority: 2]" in log.get("_raw", ""))
    p3 = sum(1 for log in logs if "[Priority: 3]" in log.get("_raw", ""))

    score = 1 - (PENALTY_SNORT_1 * p1 + PENALTY_SNORT_2 * p2)

    # Bonus: se nessun P1/P2, e ci sono log, premia comportamento "pulito"
    if p1 == 0 and p2 == 0 and len(logs) > 0:
        bonus = 0.05 + (0.01 * min(p3, 5))  # massimo bonus 0.10
        score += bonus
        logging.info(f"Snort: bonus {bonus:.2f} per traffico monitorato con solo Priority 3")

    score = min(max(score, 0.0), 1.0)
    logging.info(f"Snort score = {score:.2f} (P1={p1}, P2={p2}, P3={p3})")
    return score

def score_pep(ip_client, username):
    # Accessi negati
    fail_logs_ip = splunk_search("pep", f"IP: {ip_client} Accesso: negato", 20, earliest_time="-10m")
    fail_logs_user = splunk_search("pep", f"Utente: {username} Accesso: negato", 20, earliest_time="-10m")
    fail_score_ip = max(0, 1 - PENALTY_PEP_FAIL_IP * len(fail_logs_ip))
    fail_score_user = max(0, 1 - PENALTY_PEP_FAIL_USER * len(fail_logs_user))

    # Accessi concessi (positivi)
    success_logs_user = splunk_search("pep", f"Utente: {username} Accesso: concesso", 20, earliest_time="-10m")
    success_logs_ip = splunk_search("pep", f"IP: {ip_client} Accesso: concesso", 20, earliest_time="-10m")
    success_bonus = BONUS_PEP * (len(success_logs_user) + len(success_logs_ip))
    success_bonus = min(success_bonus, 0.1)  # max bonus

    # Score medio tra IP e User, poi aggiungo bonus
    base_score = (fail_score_ip + fail_score_user) / 2
    score = min(base_score + success_bonus, 1.0)

    logging.info(
        f"PEP score = {score:.2f} (fail_ip={len(fail_logs_ip)}, fail_user={len(fail_logs_user)}, "
        f"success_user={len(success_logs_user)}, success_ip={len(success_logs_ip)}, bonus={success_bonus:.2f})"
    )
    return score

def calculate_trust(context):
    ruolo = context.get("soggetto", "").lower()
    rete = context.get("rete", "").lower()
    dispositivo = context.get("dispositivo", "").lower()
    ip_client = context.get("ip_client", "").lower()
    username = context.get("username", "").lower()

    ruolo_score = BASE_TRUST.get(ruolo, 0.2)
    rete_score = NETWORK_SCORE.get(rete, 0.3)
    dispositivo_score = DEVICE_SCORE.get(dispositivo, 0.5)

    squid_logs = splunk_search("squid", ip_client, 10, earliest_time="-2m")
    squid_score = score_squid(squid_logs)

    snort_logs = splunk_search("snort", '10.10.1.253', 10, earliest_time="-2m")
    snort_score = score_snort(snort_logs)

    pep_score = score_pep(ip_client, username)

    trust = (
        WEIGHTS["ruolo"] * ruolo_score +
        WEIGHTS["rete"] * rete_score +
        WEIGHTS["dispositivo"] * dispositivo_score +
        WEIGHTS["squid"] * squid_score +
        WEIGHTS["snort"] * snort_score +
        WEIGHTS["pep"] * pep_score
    )

    trust = round(min(max(trust, TRUST_FLOOR), TRUST_CAP), 2)

    logging.info(f"Trust finale calcolata: {trust:.2f}")
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