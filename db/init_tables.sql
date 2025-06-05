CREATE TABLE IF NOT EXISTS access_logs (
    id SERIAL PRIMARY KEY,
    access_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    device VARCHAR(100) CHECK(device IN ('Aziendale', 'Privato')) NOT NULL,
    network VARCHAR(100) CHECK(network IN ('Aziendale', 'VPN', 'Domestica', 'Pubblica')) NOT NULL,
    operation VARCHAR(100) CHECK(operation IN ('Lettura', 'Scrittura')) NOT NULL,
    resource_acc VARCHAR(100) CHECK(resource_acc IN ('Sensibile', 'Non sensibile')) NOT NULL,
    source_ip VARCHAR(45),
    username_attempted VARCHAR(50),  -- se fornito, anche se non valido
    outcome BOOLEAN DEFAULT 0
);

CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    user_role VARCHAR(100) CHECK(user IN ('Amministratore', 'Personale', 'Guest', 'Sconosciuto')) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE tipi_risorse (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(255) UNIQUE NOT NULL,  -- Es: "Cartella Clinica", "Referto di laboratorio", ecc.
    descrizione TEXT,
    tipo_risorsa VARCHAR(50) CHECK(tipo_risorsa IN ('sensibile', 'non_sensibile'))  -- 'sensibile' o 'non_sensibile'
);

INSERT INTO tipi_risorse (nome, descrizione, tipo_risorsa)
VALUES 
    ('Cartella Clinica', 'Cartella contenente la storia clinica del paziente, diagnosi, trattamenti', 'sensibile'),
    ('Diagnosi Pazienti', 'Referti di laboratorio relativi ai pazienti', 'sensibile'),
    ('Orario di apertura', 'Orario di apertura uffici amministrativi', 'non_sensibile'),
    ('Orario di visita', 'Orari di visita per i parenti dei pazienti', 'non_sensibile');


