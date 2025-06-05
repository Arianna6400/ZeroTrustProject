from flask import Flask, request, jsonify

app = Flask(__name__)

def valuta_fiducia(soggetto, rete, dispositivo):
    punteggio = 0

    # Valutazione soggetto
    if soggetto.startswith("admin"):
        punteggio += 0.4
    elif soggetto.startswith("personale"):
        punteggio += 0.3
    elif soggetto.startswith("guest"):
        punteggio += 0.2
    else:
        punteggio += 0.1  # sconosciuto

    # Valutazione rete
    if rete == "Aziendale":
        punteggio += 0.3
    elif rete == "VPN":
        punteggio += 0.2
    elif rete == "Domestica":
        punteggio += 0.1
    else:
        punteggio += 0

    # Valutazione dispositivo
    if dispositivo == "Aziendale":
        punteggio += 0.3
    elif dispositivo == "Privato":
        punteggio += 0.1
    else:
        punteggio += 0

    # Normalizza massimo a 1.0
    return min(punteggio, 1.0)

@app.route('/valuta', methods=['POST'])
def valuta():
    contesto = request.get_json()

    soggetto = contesto.get("soggetto", "")
    rete = contesto.get("rete", "")
    dispositivo = contesto.get("dispositivo", "")
    operazione = contesto.get("operazione", "")
    risorsa = contesto.get("risorsa", "")

    livello_fiducia = valuta_fiducia(soggetto, rete, dispositivo)

    return jsonify({"fiducia": livello_fiducia})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
