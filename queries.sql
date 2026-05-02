-- queries.sql -- DBS Zadanie 3, Správa kina
-- Autori: Peter Mezei, David Blanco
--
-- Procesy:
--   1. Operačný   -- Transakčný predaj lístkov  (Z1, Scenár 2)
--   2. Analytický -- Štatistika predajnosti     (Z1, Scenár 4)
--
-- Pred spustením: aplikuj schema.sql, naseeduj DB cez seed/main.py
-- a v psql nastav potrebné parametre cez \set.


-- ============================================================================
-- Process 1 -- Transakčný predaj lístkov
-- Parametre: :id_premietanie, :id_sedadlo
-- Pohľad vw_dostupne_sedadla je definovaný v schema.sql.
-- ============================================================================

-- Pre-flight: vráti 1 riadok ak je sedadlo aktuálne predajné, inak 0.
SELECT id_premietanie, id_sedadlo, rad, cislo, sala, cena
FROM   vw_dostupne_sedadla
WHERE  id_premietanie = :id_premietanie
  AND  id_sedadlo     = :id_sedadlo;

-- Atomický predaj cez pohľad: vloží práve 1 riadok ak sedadlo spĺňa
-- (a) patrí do sály daného premietania, (b) nie je predané, (c) premietanie
-- ešte neskončilo. Inak vráti 0 riadkov bez chyby.
INSERT INTO listky (id_premietanie, id_sedadlo)
SELECT v.id_premietanie,
       v.id_sedadlo
FROM   vw_dostupne_sedadla v
WHERE  v.id_premietanie = :id_premietanie
  AND  v.id_sedadlo     = :id_sedadlo
RETURNING id, id_premietanie, id_sedadlo, cas_predaja;


-- ============================================================================
-- Process 2 -- Štatistika predajnosti filmov
-- Parametre: :od, :do  (DATE alebo TIMESTAMP, vrátane :do)
-- ============================================================================

WITH kapacita_kinosaly AS (
    SELECT  k.id        AS id_kinosala,
            COUNT(s.id) AS kapacita
    FROM    kinosaly k
    JOIN    sedadla  s ON s.id_kinosala = k.id
    GROUP BY k.id
),
filtrovane_premietania AS (
    SELECT  p.id,
            p.id_film,
            p.cena,
            kk.kapacita
    FROM    premietania p
    JOIN    kapacita_kinosaly kk ON kk.id_kinosala = p.id_kinosala
    WHERE   p.cas_zaciatku >= :od
      AND   p.cas_zaciatku <  (:do::timestamp + INTERVAL '1 day')
),
predane_na_premietanie AS (
    SELECT  l.id_premietanie,
            COUNT(*) AS predane_listky
    FROM    listky l
    GROUP BY l.id_premietanie
),
predaj_film AS (
    SELECT  f.id                              AS id_film,
            f.nazov                           AS nazov_filmu,
            fp.id                             AS id_premietania,
            fp.cena                           AS cena_premietania,
            fp.kapacita                       AS kapacita,
            COALESCE(pnp.predane_listky, 0)   AS predane_listky
    FROM    filtrovane_premietania fp
    JOIN    filmy f                ON f.id = fp.id_film
    LEFT JOIN predane_na_premietanie pnp
                                  ON pnp.id_premietanie = fp.id
)
SELECT
    nazov_filmu,
    COUNT(*)                                  AS pocet_premietani_s_predajom,
    SUM(predane_listky)                       AS predane_listky_spolu,
    ROUND(SUM(predane_listky * cena_premietania), 2)
                                              AS trzba_spolu_eur,
    ROUND(AVG(predane_listky), 2)             AS priemer_listkov_na_premietanie,
    ROUND(
        SUM(predane_listky * cena_premietania) /
        NULLIF(SUM(predane_listky), 0),
        2
    )                                         AS priemerna_cena_predaneho_listka_eur,
    ROUND(
        100.0 * SUM(predane_listky) /
        NULLIF(SUM(kapacita), 0),
        2
    )                                         AS obsadenost_pct,
    RANK() OVER (
        ORDER BY SUM(predane_listky * cena_premietania) DESC
    )                                         AS poradie_podla_trzby
FROM   predaj_film
GROUP BY nazov_filmu
ORDER BY trzba_spolu_eur DESC,
         predane_listky_spolu DESC;
