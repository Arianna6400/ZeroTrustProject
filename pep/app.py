from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

PDP_URL = 'http://pdp:8001/authorize'

@app.route('/access', methods=['POST'])
def access_request():
    data = request.json
    response = requests.post(PDP_URL, json=data)

    if response.status_code == 200 and response.json().get('authorized'):
        return jsonify({'message': 'Access granted'}), 200
    else:
        return jsonify({'message': 'Access denied'}), 403
    
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)