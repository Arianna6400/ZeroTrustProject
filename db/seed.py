import psycopg2
from faker import Faker
import random
import os

conn = psycopg2.connect(
    host=os.environ['DB_HOST'],
    port=os.environ['DB_PORT'],
    dbname=os.environ['DB_NAME'],
    user=os.environ['DB_USER'],
    password=os.environ['DB_PASSWORD']
)

cursor = conn.cursor()
fake = Faker()

def seed_users():
    for _ in range(100):  # Numero di utenti da generare
        username = fake.user_name()
        password_hash = fake.sha256()  # Utilizza un hash fittizio per la password
        user_role = random.choice(['Amministratore', 'Personale', 'Guest', 'Sconosciuto'])
        cursor.execute("""
            INSERT INTO users (username, password_hash, user_role) 
            VALUES (%s, %s, %s)
        """, (username, password_hash, user_role))
    conn.commit()

def seed_access_logs():
    # Recupera gli user_id esistenti dalla tabella users
    cursor.execute("SELECT id FROM users")
    user_ids = [row[0] for row in cursor.fetchall()]  # Ottieni una lista di tutti gli user_id
    
    for _ in range(1000):  # Numero di log di accesso da generare
        user_id = random.choice(user_ids)  # Scegli un user_id che esiste nella tabella
        device = random.choice(['Aziendale', 'Privato'])
        network = random.choice(['Aziendale', 'VPN', 'Domestica', 'Pubblica'])
        operation = random.choice(['Lettura', 'Scrittura'])
        resource_acc = random.choice(['Sensibile', 'Non sensibile'])
        source_ip = fake.ipv4()
        username_attempted = fake.user_name()
        outcome = random.choice([True, False])

        cursor.execute("""
            INSERT INTO access_logs (user_id, device, network, operation, resource_acc, source_ip, username_attempted, outcome)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (user_id, device, network, operation, resource_acc, source_ip, username_attempted, outcome))
    conn.commit()


def seed_tipirrisorse():
    risorse = [
        ('Cartella Clinica', 'Cartella contenente la storia clinica del paziente, diagnosi, trattamenti', 'sensibile'),
        ('Diagnosi Pazienti', 'Referti di laboratorio relativi ai pazienti', 'sensibile'),
        ('Dati anagrafici pazienti', 'Informazioni personali dei pazienti', 'sensibile'),
        ('Prescrizioni', 'Farmaci prescritti dal medico', 'sensibile'),
        ('Orario di apertura', 'Orario di apertura uffici amministrativi', 'non_sensibile'),
        ('Orario di visita', 'Orari di visita per i parenti dei pazienti', 'non_sensibile')
    ]
    
    for nome, descrizione, tipo_risorsa in risorse:
        # Verifica se il nome della risorsa esiste già nella tabella
        cursor.execute("SELECT 1 FROM tipi_risorse WHERE nome = %s", (nome,))
        if cursor.fetchone() is None:  # Se non esiste, inserisci
            cursor.execute("""
                INSERT INTO tipi_risorse (nome, descrizione, tipo_risorsa)
                VALUES (%s, %s, %s)
            """, (nome, descrizione, tipo_risorsa))
        else:
            print(f"Risorsa '{nome}' già presente. Skipping...")
    conn.commit()

seed_users()
seed_access_logs()
seed_tipirrisorse()

cursor.close()
conn.close()

print("Seeding completato!")
