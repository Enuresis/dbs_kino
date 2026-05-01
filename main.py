import os
import random
from collections import defaultdict
from datetime import date, datetime, time, timedelta

import psycopg2
from psycopg2.extras import execute_values


DB_PARAMS = {
    "dbname": os.getenv("DB_NAME", "Zadanie 3"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "FuwaFuwaTime"),
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", "5432")),
}

RNG_SEED = 42
TARGET_TOTAL_ROWS = 10_000
RESET_TABLES = True


def random_datetime_between(start_dt, end_dt):
    span_seconds = int((end_dt - start_dt).total_seconds())
    return start_dt + timedelta(seconds=random.randint(0, span_seconds))


def intervals_overlap(start_a, end_a, start_b, end_b):
    return start_a < end_b and start_b < end_a


def batch_insert(cur, query, rows, page_size=1000):
    if not rows:
        return
    execute_values(cur, query, rows, page_size=page_size)


def fetch_ids(cur, table_name):
    cur.execute(f"SELECT id FROM {table_name} ORDER BY id")
    return [row[0] for row in cur.fetchall()]


def reset_all_tables(cur):
    cur.execute(
        """
        TRUNCATE TABLE
            listky,
            ulohy,
            premietania,
            sedadla,
            zamestnanci,
            filmy,
            kinosaly,
            typy_uloh,
            typy_uvazku,
            zanre
        RESTART IDENTITY CASCADE
        """
    )


def seed_reference_tables(cur):
    genres = [
        "Akcny",
        "Dobrodruzny",
        "Drama",
        "Komedia",
        "Romanticky",
        "Sci-fi",
        "Horor",
        "Animovany",
        "Thriller",
        "Dokument",
    ]
    contract_types = [("Plny uvazok",), ("Polovicny uvazok",), ("Brigada",)]
    task_types = [
        ("Predaj listkov",),
        ("Kontrola vstupeniek",),
        ("Upratovanie saly",),
        ("Technicka podpora projekcie",),
        ("Obsluha baru",),
        ("Manazerska sluzba",),
    ]

    batch_insert(cur, "INSERT INTO zanre (nazov) VALUES %s", [(g,) for g in genres])
    batch_insert(cur, "INSERT INTO typy_uvazku (uvazok) VALUES %s", contract_types)
    batch_insert(cur, "INSERT INTO typy_uloh (nazov_ulohy) VALUES %s", task_types)

    return {
        "zanre": len(genres),
        "typy_uvazku": len(contract_types),
        "typy_uloh": len(task_types),
    }


def seed_filmy(cur, genre_ids, count=120):
    adjectives = [
        "Posledny",
        "Tichy",
        "Nekonecny",
        "Temny",
        "Strateny",
        "Zabudnuty",
        "Tajomny",
        "Divoky",
        "Skryty",
        "Ledovy",
        "Ohnivy",
        "Nocturny",
    ]
    nouns = [
        "Pribeh",
        "Lovec",
        "Mesto",
        "Svetlo",
        "Tieň",
        "Horizont",
        "Experiment",
        "Most",
        "Hrad",
        "Signal",
        "Vlak",
        "Ostrov",
        "Misia",
        "Svedok",
    ]
    subtitles = [
        "Nove zaciatky",
        "Posledna kapitola",
        "Bez navratu",
        "V tieni pravdy",
        "Za hranou casu",
        "V hlavnej ulohe noc",
        "Mimo pravidiel",
        "Nad mestom",
    ]

    rows = []
    used_titles = set()
    while len(rows) < count:
        base = f"{random.choice(adjectives)} {random.choice(nouns)}"
        if random.random() < 0.3:
            title = f"{base}: {random.choice(subtitles)}"
        else:
            title = base
        if title in used_titles:
            continue
        used_titles.add(title)
        rows.append(
            (
                title,
                random.randint(85, 175),
                random.choice(genre_ids),
                random.choice([0, 12, 15, 18]),
            )
        )

    batch_insert(
        cur,
        """
        INSERT INTO filmy (nazov, dlzka_minut, id_zaner, vekovy_limit)
        VALUES %s
        """,
        rows,
    )
    return len(rows)


def seed_kinosaly(cur):
    halls = [
        ("SALA 1", "2D"),
        ("SALA 2", "2D"),
        ("SALA 3", "2D"),
        ("SALA 4", "3D"),
        ("SALA 5", "3D"),
        ("VIP SALA", "2D"),
        ("RODINNA SALA", "2D"),
        ("PREMIUM IMAX", "3D"),
    ]
    batch_insert(
        cur,
        "INSERT INTO kinosaly (nazov, typ_premietania) VALUES %s",
        halls,
    )
    return len(halls)


def seed_sedadla(cur, halls):
    rows = []
    hall_seat_target = {
        "SALA 1": (12, 14),
        "SALA 2": (11, 14),
        "SALA 3": (10, 14),
        "SALA 4": (13, 15),
        "SALA 5": (12, 15),
        "VIP SALA": (7, 10),
        "RODINNA SALA": (8, 11),
        "PREMIUM IMAX": (14, 16),
    }
    for hall_id, hall_name in halls:
        rows_count, seats_in_row = hall_seat_target[hall_name]
        for row_no in range(1, rows_count + 1):
            for seat_no in range(1, seats_in_row + 1):
                rows.append((hall_id, row_no, seat_no))

    batch_insert(
        cur,
        "INSERT INTO sedadla (id_kinosala, rad, cislo) VALUES %s",
        rows,
    )
    return len(rows)


def seed_zamestnanci(cur, contract_type_ids, count=120):
    first_names_m = [
        "Martin",
        "Peter",
        "Lukas",
        "Tomas",
        "Jozef",
        "Marek",
        "Milan",
        "Andrej",
        "Michal",
        "Jakub",
    ]
    first_names_f = [
        "Lucia",
        "Petra",
        "Jana",
        "Martina",
        "Veronika",
        "Katarina",
        "Simona",
        "Nikola",
        "Eva",
        "Michaela",
    ]
    surnames = [
        "Novak",
        "Kovac",
        "Horvath",
        "Varga",
        "Toth",
        "Balaz",
        "Molnar",
        "Kral",
        "Hudak",
        "Urban",
        "Mikula",
        "Benko",
    ]

    rows = []
    for _ in range(count):
        if random.random() < 0.5:
            name = random.choice(first_names_m)
            surname = random.choice(surnames)
        else:
            name = random.choice(first_names_f)
            surname = random.choice(surnames) + random.choice(["ova", ""])

        # Most employees have valid documents, some have expired ones.
        if random.random() < 0.8:
            start_valid = date.today() + timedelta(days=30)
            end_valid = date.today() + timedelta(days=365 * 4)
            valid_doc = start_valid + timedelta(
                days=random.randint(0, (end_valid - start_valid).days)
            )
        else:
            expired_start = date.today() - timedelta(days=365 * 4)
            expired_end = date.today() - timedelta(days=1)
            valid_doc = expired_start + timedelta(
                days=random.randint(0, (expired_end - expired_start).days)
            )
        rows.append((name, surname, random.choice(contract_type_ids), valid_doc))

    batch_insert(
        cur,
        """
        INSERT INTO zamestnanci (meno, priezvisko, id_typ_uvazku, platnost_zdrav_preukazu)
        VALUES %s
        """,
        rows,
    )
    return len(rows)


def seed_premietania(cur, films, halls, count_days=90):
    film_len_by_id = {film_id: film_length for film_id, film_length in films}
    rows = []

    start_date = date.today() - timedelta(days=30)
    end_date = start_date + timedelta(days=count_days)

    for hall_id, _hall_name in halls:
        current_date = start_date
        while current_date < end_date:
            # Build day schedule sequentially to guarantee no overlaps in one hall.
            current_start = datetime.combine(current_date, time(10, 0))
            day_end = datetime.combine(current_date, time(23, 30))
            min_turnover = 15
            max_turnover = 30

            while current_start < day_end:
                film_id = random.choice(list(film_len_by_id.keys()))
                film_length = film_len_by_id[film_id]
                screening_end = current_start + timedelta(minutes=film_length)
                if screening_end > day_end:
                    break
                base_price = random.uniform(6.0, 13.5)
                if current_start.weekday() >= 4:
                    base_price += 0.8
                if current_start.hour >= 18:
                    base_price += 0.7
                screening_price = round(base_price, 2)
                rows.append((film_id, hall_id, current_start, screening_end, screening_price))
                turnover = random.randint(min_turnover, max_turnover)
                current_start = screening_end + timedelta(minutes=turnover)
            current_date += timedelta(days=1)

    batch_insert(
        cur,
        """
        INSERT INTO premietania (id_film, id_kinosala, cas_zaciatku, cas_konca, cena)
        VALUES %s
        """,
        rows,
    )
    return len(rows)


def seed_ulohy(
    cur,
    employees,
    halls,
    task_type_rows,
    valid_doc_employee_ids,
    count=900,
):
    rows = []
    tasks_per_employee = defaultdict(list)
    now = datetime.now()
    begin_range = now - timedelta(days=45)
    end_range = now + timedelta(days=45)
    food_keywords = ("bar", "obcerstven")
    food_task_type_ids = {
        task_id
        for task_id, task_name in task_type_rows
        if any(keyword in task_name.lower() for keyword in food_keywords)
    }
    valid_doc_employee_ids = set(valid_doc_employee_ids)

    for _ in range(count):
        inserted = False
        for _attempt in range(250):
            task_type_id, _task_name = random.choice(task_type_rows)
            if task_type_id in food_task_type_ids:
                eligible_employees = list(valid_doc_employee_ids)
            else:
                eligible_employees = employees
            if not eligible_employees:
                raise RuntimeError("No eligible employees available for task assignment.")

            employee_id = random.choice(eligible_employees)
            hall_id = random.choice(halls + [None, None, None])
            task_start = random_datetime_between(begin_range, end_range).replace(
                minute=0, second=0, microsecond=0
            )
            duration_hours = random.choice([2, 4, 6, 8])
            task_end = task_start + timedelta(hours=duration_hours)

            overlaps = any(
                intervals_overlap(task_start, task_end, existing_start, existing_end)
                for existing_start, existing_end in tasks_per_employee[employee_id]
            )
            if overlaps:
                continue

            rows.append((employee_id, hall_id, task_type_id, task_start, task_end))
            tasks_per_employee[employee_id].append((task_start, task_end))
            inserted = True
            break

        if not inserted:
            raise RuntimeError(
                "Unable to generate non-overlapping employee tasks with current parameters."
            )

    batch_insert(
        cur,
        """
        INSERT INTO ulohy (id_zamestnanec, id_kinosala, id_typ_ulohy, cas_zaciatku, cas_konca)
        VALUES %s
        """,
        rows,
    )
    return len(rows)


def seed_listky(cur, screenings, seats_by_hall, minimum_count=7000):
    rows = []
    for screening_id, hall_id, start_at in screenings:
        all_seats = seats_by_hall[hall_id]
        # Smaller occupancy for morning slots, larger for evenings/weekends.
        if start_at.hour < 14:
            occupancy = random.uniform(0.15, 0.45)
        elif start_at.hour < 18:
            occupancy = random.uniform(0.30, 0.70)
        else:
            occupancy = random.uniform(0.45, 0.95)
        if start_at.weekday() >= 4:
            occupancy += 0.05
        occupancy = min(occupancy, 0.98)

        sold_count = max(1, int(len(all_seats) * occupancy))
        sold_seats = random.sample(all_seats, k=sold_count)

        for seat_id in sold_seats:
            sold_at = start_at - timedelta(
                hours=random.randint(1, 240), minutes=random.randint(0, 59)
            )
            rows.append((screening_id, seat_id, sold_at))

    if len(rows) < minimum_count:
        raise RuntimeError(
            f"Not enough generated tickets: {len(rows)} < required {minimum_count}."
        )

    batch_insert(
        cur,
        """
        INSERT INTO listky (id_premietanie, id_sedadlo, cas_predaja)
        VALUES %s
        """,
        rows,
    )
    return len(rows)


def validate_generated_data(cur):
    checks = [
        (
            "Duplicate seat sold for one screening",
            """
            SELECT 1
            FROM listky
            GROUP BY id_premietanie, id_sedadlo
            HAVING COUNT(*) > 1
            LIMIT 1
            """,
        ),
        (
            "Overlapping screenings in one hall",
            """
            SELECT 1
            FROM premietania p1
            JOIN premietania p2
              ON p1.id_kinosala = p2.id_kinosala
             AND p1.id < p2.id
             AND p1.cas_zaciatku < p2.cas_konca
             AND p2.cas_zaciatku < p1.cas_konca
            LIMIT 1
            """,
        ),
        (
            "Tickets sold above hall capacity",
            """
            WITH kapacita AS (
                SELECT id_kinosala, COUNT(*) AS kapacita
                FROM sedadla
                GROUP BY id_kinosala
            ),
            predane AS (
                SELECT l.id_premietanie, COUNT(*) AS predane
                FROM listky l
                GROUP BY l.id_premietanie
            )
            SELECT 1
            FROM predane p
            JOIN premietania pr ON pr.id = p.id_premietanie
            JOIN kapacita k ON k.id_kinosala = pr.id_kinosala
            WHERE p.predane > k.kapacita
            LIMIT 1
            """,
        ),
        (
            "Ticket seat does not belong to screening hall",
            """
            SELECT 1
            FROM listky l
            JOIN premietania p ON p.id = l.id_premietanie
            JOIN sedadla s ON s.id = l.id_sedadlo
            WHERE s.id_kinosala <> p.id_kinosala
            LIMIT 1
            """,
        ),
        (
            "Food task assigned to employee with expired document",
            """
            SELECT 1
            FROM ulohy u
            JOIN typy_uloh tu ON tu.id = u.id_typ_ulohy
            JOIN zamestnanci z ON z.id = u.id_zamestnanec
            WHERE (LOWER(tu.nazov_ulohy) LIKE '%bar%' OR LOWER(tu.nazov_ulohy) LIKE '%obcerstven%')
              AND z.platnost_zdrav_preukazu < CURRENT_DATE
            LIMIT 1
            """,
        ),
        (
            "Employee has overlapping tasks",
            """
            SELECT 1
            FROM ulohy u1
            JOIN ulohy u2
              ON u1.id_zamestnanec = u2.id_zamestnanec
             AND u1.id < u2.id
             AND u1.cas_zaciatku < u2.cas_konca
             AND u2.cas_zaciatku < u1.cas_konca
            LIMIT 1
            """,
        ),
    ]

    for check_name, query in checks:
        cur.execute(query)
        if cur.fetchone() is not None:
            raise RuntimeError(f"Constraint validation failed: {check_name}")


def main():
    random.seed(RNG_SEED)
    conn = psycopg2.connect(**DB_PARAMS)
    counts = defaultdict(int)

    try:
        with conn.cursor() as cur:
            if RESET_TABLES:
                reset_all_tables(cur)

            counts.update(seed_reference_tables(cur))

            genre_ids = fetch_ids(cur, "zanre")
            counts["filmy"] = seed_filmy(cur, genre_ids, count=30)

            counts["kinosaly"] = seed_kinosaly(cur)
            cur.execute("SELECT id, nazov FROM kinosaly ORDER BY id")
            halls = cur.fetchall()

            counts["sedadla"] = seed_sedadla(cur, halls)

            contract_ids = fetch_ids(cur, "typy_uvazku")
            counts["zamestnanci"] = seed_zamestnanci(cur, contract_ids, count=40)

            cur.execute("SELECT id, dlzka_minut FROM filmy")
            films = cur.fetchall()
            counts["premietania"] = seed_premietania(cur, films, halls, count_days=30)

            employee_ids = fetch_ids(cur, "zamestnanci")
            hall_ids = [hall_id for hall_id, _ in halls]
            cur.execute("SELECT id, nazov_ulohy FROM typy_uloh")
            task_type_rows = cur.fetchall()
            cur.execute(
                """
                SELECT id
                FROM zamestnanci
                WHERE platnost_zdrav_preukazu >= CURRENT_DATE
                """
            )
            valid_doc_employee_ids = [row[0] for row in cur.fetchall()]
            counts["ulohy"] = seed_ulohy(
                cur,
                employee_ids,
                hall_ids,
                task_type_rows,
                valid_doc_employee_ids,
                count=120,
            )

            cur.execute(
                """
                SELECT p.id, p.id_kinosala, p.cas_zaciatku
                FROM premietania p
                ORDER BY p.id
                """
            )
            screenings = cur.fetchall()
            cur.execute("SELECT id, id_kinosala FROM sedadla")
            seats_raw = cur.fetchall()
            seats_by_hall = defaultdict(list)
            for seat_id, hall_id in seats_raw:
                seats_by_hall[hall_id].append(seat_id)

            counts["listky"] = seed_listky(cur, screenings, seats_by_hall, 7000)
            validate_generated_data(cur)

            total_rows = sum(counts.values())
            if total_rows < TARGET_TOTAL_ROWS:
                raise RuntimeError(
                    f"Total inserted rows {total_rows} is less than required {TARGET_TOTAL_ROWS}."
                )

            conn.commit()

        print("Seeding completed successfully.")
        print("Inserted rows by table:")
        for table_name in sorted(counts.keys()):
            print(f"  {table_name}: {counts[table_name]}")
        print(f"Total inserted rows: {sum(counts.values())}")

    except Exception as exc:
        conn.rollback()
        print(f"Seeding failed: {exc}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()