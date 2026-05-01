-- Predajnost filmov za zvolene obdobie (podla casu premietania)
-- Parametre: '<od_datum>', '<do_datum>' (napr. '2026-04-01', '2026-04-30')
-- Poznamka: Tato verzia najskor odfiltruje premietania v intervale,
-- potom prirata listky po id_premietanie.

-- 1) Kompozitny index pre filter + join/agregaciu premietani
CREATE INDEX IF NOT EXISTS idx_premietania_interval_film
    ON premietania (cas_zaciatku, id, id_film);
DROP INDEX idx_premietania_interval_film;

-- 2) Index pre rychly pocet listkov na premietanie
CREATE INDEX IF NOT EXISTS idx_listky_premietanie
    ON listky (id_premietanie);
DROP INDEX idx_listky_premietanie;
-- 3) Covering index pre finalny join filmu a citanie nazvu
CREATE INDEX IF NOT EXISTS idx_filmy_id_nazov
    ON filmy (id) INCLUDE (nazov);
DROP INDEX idx_filmy_id_nazov;

EXPLAIN (ANALYZE, BUFFERS)
WITH filtrovane_premietania AS (
    SELECT
        p.id,
        p.id_film,
        p.cena
    FROM premietania p
    WHERE p.cas_zaciatku >= '2026-04-01'
      AND p.cas_zaciatku < ('2026-04-05'::timestamp + INTERVAL '1 day')
),
predane_na_premietanie AS (
    SELECT
        l.id_premietanie,
        COUNT(*) AS predane_listky
    FROM listky l
    GROUP BY l.id_premietanie
),
predaj_film AS (
    SELECT
        f.id AS id_film,
        f.nazov AS nazov_filmu,
        fp.id AS id_premietania,
        fp.cena AS cena_premietania,
        COALESCE(pnp.predane_listky, 0) AS predane_listky
    FROM filtrovane_premietania fp
    JOIN filmy f ON f.id = fp.id_film
    LEFT JOIN predane_na_premietanie pnp ON pnp.id_premietanie = fp.id
)
SELECT
    nazov_filmu,
    COUNT(*) AS pocet_premietani_s_predajom,
    SUM(predane_listky) AS predane_listky_spolu,
    ROUND(SUM(predane_listky * cena_premietania), 2) AS trzba_spolu_eur,
    ROUND(AVG(predane_listky), 2) AS priemer_listkov_na_premietanie,
    ROUND(
        SUM(predane_listky * cena_premietania) / NULLIF(SUM(predane_listky), 0),
        2
    ) AS priemerna_cena_predaneho_listka_eur,
    RANK() OVER (ORDER BY SUM(predane_listky * cena_premietania) DESC) AS poradie_podla_trzby
FROM predaj_film
GROUP BY nazov_filmu
ORDER BY trzba_spolu_eur DESC, predane_listky_spolu DESC;

-- no indices: 12.355ms