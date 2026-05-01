DROP TABLE IF EXISTS listky;
DROP TABLE IF EXISTS ulohy;
DROP TABLE IF EXISTS premietania;
DROP TABLE IF EXISTS sedadla;
DROP TABLE IF EXISTS zamestnanci;
DROP TABLE IF EXISTS filmy;
DROP TABLE IF EXISTS kinosaly;
DROP TABLE IF EXISTS typy_uloh;
DROP TABLE IF EXISTS typy_uvazku;
DROP TABLE IF EXISTS zanre;
DROP TYPE IF EXISTS typ_premietania;


CREATE TYPE typ_premietania AS ENUM ('2D', '3D');

CREATE TABLE zanre (
    id SERIAL PRIMARY KEY,
    nazov VARCHAR(50)
);

CREATE TABLE typy_uvazku (
    id SERIAL PRIMARY KEY,
    uvazok VARCHAR(20)
);

CREATE TABLE typy_uloh (
    id SERIAL PRIMARY KEY,
    nazov_ulohy VARCHAR(50)
);

CREATE TABLE filmy (
    id SERIAL PRIMARY KEY,
    nazov VARCHAR(100) NOT NULL,
    dlzka_minut INT NOT NULL CHECK (dlzka_minut > 0),
    id_zaner INT,
    vekovy_limit INT DEFAULT 0,
    FOREIGN KEY (id_zaner) REFERENCES zanre (id)
);

CREATE TABLE kinosaly (
    id SERIAL PRIMARY KEY,
    nazov VARCHAR(50) NOT NULL UNIQUE,
    typ_premietania typ_premietania
);

CREATE TABLE sedadla (
    id SERIAL PRIMARY KEY,
    id_kinosala INT NOT NULL,
    rad INT NOT NULL CHECK (rad > 0),
    cislo INT NOT NULL CHECK (cislo > 0),
    FOREIGN KEY (id_kinosala) REFERENCES kinosaly (id) ON DELETE CASCADE,
    UNIQUE (id_kinosala, rad, cislo)
);

CREATE TABLE premietania (
    id SERIAL PRIMARY KEY,
    id_film INT NOT NULL,
    id_kinosala INT NOT NULL,
    cas_zaciatku TIMESTAMP NOT NULL,
    cas_konca TIMESTAMP NOT NULL,
    cena NUMERIC(5, 2) NOT NULL CHECK (cena > 0),
    FOREIGN KEY (id_film) REFERENCES filmy (id) ON DELETE RESTRICT,
    FOREIGN KEY (id_kinosala) REFERENCES kinosaly (id) ON DELETE RESTRICT
);

CREATE TABLE zamestnanci (
    id SERIAL PRIMARY KEY,
    meno VARCHAR(50) NOT NULL,
    priezvisko VARCHAR(50) NOT NULL,
    id_typ_uvazku INT NOT NULL,
    platnost_zdrav_preukazu DATE,
    FOREIGN KEY (id_typ_uvazku) REFERENCES typy_uvazku (id)
);

CREATE TABLE ulohy (
    id SERIAL PRIMARY KEY,
    id_zamestnanec INT NOT NULL,
    id_kinosala INT,
    id_typ_ulohy INT NOT NULL,
    cas_zaciatku TIMESTAMP NOT NULL,
    cas_konca TIMESTAMP NOT NULL,
    FOREIGN KEY (id_zamestnanec) REFERENCES zamestnanci (id) ON DELETE CASCADE,
    FOREIGN KEY (id_kinosala) REFERENCES kinosaly (id) ON DELETE CASCADE,
    FOREIGN KEY (id_typ_ulohy) REFERENCES typy_uloh (id)
);

CREATE TABLE listky (
    id SERIAL PRIMARY KEY,
    id_premietanie INT NOT NULL,
    id_sedadlo INT NOT NULL,
    cas_predaja TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (id_premietanie) REFERENCES premietania (id) ON DELETE RESTRICT,
    FOREIGN KEY (id_sedadlo) REFERENCES sedadla (id) ON DELETE RESTRICT,
    UNIQUE (id_premietanie, id_sedadlo)
);