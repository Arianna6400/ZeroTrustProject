CREATE TABLE IF NOT EXISTS access_logs (
    id SERIAL PRIMARY KEY;
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    user VARCHAR(100) CHECK(user IN ('Amministratore', 'Personale', 'Guest', 'Sconosciuto')) NOT NULL,
    device VARCHAR(100) CHECK(device IN ('Aziendale', 'Privato')) NOT NULL,
    network VARCHAR(100) CHECK(network IN ('Aziendale', 'VPN', 'Domestica', 'Pubblica')) NOT NULL,
    operation VARCHAR(100) CHECK(operation IN ('Lettura', 'Scrittura')) NOT NULL,
    resource_acc VARCHAR(100) CHECK(resource_acc IN ('Sensibile', 'Non sensibile')) NOT NULL
);