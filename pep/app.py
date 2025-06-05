from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# Funzione di esempio per determinare la soglia minima richiesta
def get_threshold(operazione, risorsa):
    if risorsa == "sensibile":
        return 0.8 if operazione == "scrittura" else 0.6
    else:
        return 0.5 if operazione == "scrittura" else 0.3

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

    # 3. Costruisci il contesto per il PDP
    contesto = {
        "soggetto": username,
        "rete": rete,
        "dispositivo": dispositivo,
        "operazione": operazione,
        "risorsa": risorsa
    }

    # 4. Chiedi valutazione al PDP
    try:
        risposta = requests.post("http://0.0.0.0:5001/valuta", json=contesto)
        risposta.raise_for_status()
        fiducia = risposta.json().get("fiducia", 0)
    except Exception as e:
        return jsonify({"errore": f"Errore nella valutazione PDP: {str(e)}"}), 500

    # 5. Valuta contro soglia
    soglia = get_threshold(operazione, risorsa)
    if fiducia >= soglia:
        # Esegui l'azione autorizzata sul DB (placeholder)
        return jsonify({"accesso": "concesso", "livello_fiducia": fiducia}), 200
    else:
        return jsonify({"accesso": "negato", "livello_fiducia": fiducia}), 403

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
