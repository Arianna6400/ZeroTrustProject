from flask import Flask, request, jsonify
import os
import psycopg2 

app = Flask(__name__)

def get_db_connection():
    return psycopg2.connect(
        host=os.environ['DB_HOST'],
        port=os.environ['DB_PORT'],
        dbname=os.environ['DB_NAME'],
        user=os.environ['DB_USER'],
        password=os.environ['DB_PASSWORD']
    )

@app.route('/authorize', methods=['POST'])
def authorize():
    data = request.json
    user_role = data.get('role')
    action = data.get('action')

    # Semplice esempio di policy: solo i medici possono scrivere
    if user_role == 'medico' or (user_role in ['paziente', 'familiare'] and action == 'read'):
        return jsonify({'authorized': True}), 200
    return jsonify({'authorized': False}), 403

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8001)