import os
import random
import secrets
import string
from datetime import date, timedelta

import psycopg

DATABASE_URL = os.getenv("DATABASE_URL")
RANDOM_GAME_TASKS = [f"Heading {index}" for index in range(1, 13)]
RANDOM_GAME_MAX_PLAYERS = 6

ROOM_SEED_DATA = [
    {
        "room_number": 101,
        "type": "Single",
        "price": 75,
    },
    {
        "room_number": 203,
        "type": "Double",
        "price": 110,
    },
    {
        "room_number": 305,
        "type": "Family",
        "price": 165,
    },
]

GUEST_SEED_DATA = [
    {
        "firstname": "Anthony",
        "lastname": "Nguyen",
        "address": "Arcada, Helsinki",
    },
    {
        "firstname": "Dennis",
        "lastname": "Bistr\u00f6m",
        "address": "Espoo, Finland",
    },
]

BOOKING_SEED_DATA = [
    {
        "guest_id": 1,
        "room_id": 1,
        "datefrom": "2026-04-10",
        "dateto": "2026-04-12",
        "addinfo": "King bed - Late check-in",
    },
    {
        "guest_id": 2,
        "room_id": 2,
        "datefrom": "2026-04-15",
        "dateto": "2026-04-18",
        "addinfo": "Twin room - Needs baby crib",
    },
]

REPORT_BOOKING_COUNT = 100
REPORT_BOOKING_PREFIX = "Report seed booking"


def get_conn():
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL is not set")
    return psycopg.connect(DATABASE_URL, autocommit=True, row_factory=psycopg.rows.dict_row)


def initialize_database():
    create_tables()
    ensure_booking_stars_column()
    insert_sample_rooms()
    insert_sample_guests()
    sync_sample_guest_names()
    insert_sample_bookings()
    insert_report_seed_bookings()
    sync_sample_booking_details()
    sync_single_night_bookings()
    create_monthly_report_view()
    create_random_game_tables()


def create_tables():
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS hotel_rooms (
                id SERIAL PRIMARY KEY,
                room_number INT NOT NULL,
                type VARCHAR(100) NOT NULL,
                price NUMERIC(10, 2) NOT NULL
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS hotel_guests (
                id SERIAL PRIMARY KEY,
                firstname VARCHAR(100) NOT NULL,
                lastname VARCHAR(100) NOT NULL,
                address VARCHAR(255) NOT NULL
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS hotel_bookings (
                id SERIAL PRIMARY KEY,
                guest_id INT NOT NULL REFERENCES hotel_guests(id),
                room_id INT NOT NULL REFERENCES hotel_rooms(id),
                datefrom DATE NOT NULL,
                dateto DATE NOT NULL,
                addinfo VARCHAR(255)
            )
            """
        )


def create_random_game_tables():
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS random_games (
                id SERIAL PRIMARY KEY,
                game_code VARCHAR(20) NOT NULL UNIQUE,
                status VARCHAR(20) NOT NULL DEFAULT 'waiting',
                max_players INT NOT NULL DEFAULT 6,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS random_game_players (
                id SERIAL PRIMARY KEY,
                game_id INT NOT NULL REFERENCES random_games(id) ON DELETE CASCADE,
                player_name VARCHAR(100) NOT NULL,
                player_order INT NOT NULL,
                is_creator BOOLEAN NOT NULL DEFAULT FALSE,
                task_one VARCHAR(100),
                task_two VARCHAR(100),
                joined_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (game_id, player_order)
            )
            """
        )


def ensure_booking_stars_column():
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
            ALTER TABLE hotel_bookings
            ADD COLUMN IF NOT EXISTS stars INT
            CHECK (stars BETWEEN 1 AND 5)
            """
        )


def insert_sample_rooms():
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) AS count FROM hotel_rooms")
        result = cur.fetchone()

        if result["count"] > 0:
            return

        for room in ROOM_SEED_DATA:
            cur.execute(
                """
                INSERT INTO hotel_rooms (room_number, type, price)
                VALUES (%(room_number)s, %(type)s, %(price)s)
                """,
                room,
            )


def insert_sample_guests():
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) AS count FROM hotel_guests")
        result = cur.fetchone()

        if result["count"] > 0:
            return

        for guest in GUEST_SEED_DATA:
            cur.execute(
                """
                INSERT INTO hotel_guests (firstname, lastname, address)
                VALUES (%(firstname)s, %(lastname)s, %(address)s)
                """,
                guest,
            )


def sync_sample_guest_names():
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
            UPDATE hotel_guests
            SET firstname = 'Anthony'
            WHERE firstname = 'Tony' AND lastname = 'Nguyen'
            """
        )
        cur.execute(
            """
            UPDATE hotel_guests
            SET firstname = 'Dennis', lastname = 'Bistr\u00f6me'
            WHERE firstname = 'Emma' AND lastname = 'Virtanen'
            """
        )


def insert_sample_bookings():
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) AS count FROM hotel_bookings")
        result = cur.fetchone()

        if result["count"] > 0:
            return

        for booking in BOOKING_SEED_DATA:
            cur.execute(
                """
                INSERT INTO hotel_bookings (guest_id, room_id, datefrom, dateto, addinfo)
                VALUES (%(guest_id)s, %(room_id)s, %(datefrom)s, %(dateto)s, %(addinfo)s)
                """,
                booking,
            )


def sync_sample_booking_details():
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
            UPDATE hotel_bookings
            SET addinfo = 'King bed - Late check-in'
            WHERE addinfo = 'Late check-in'
            """
        )
        cur.execute(
            """
            UPDATE hotel_bookings
            SET addinfo = 'Twin room - Needs baby crib'
            WHERE addinfo = 'Needs baby crib'
            """
        )


def sync_single_night_bookings():
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
            UPDATE hotel_bookings
            SET dateto = datefrom + INTERVAL '1 day'
            WHERE dateto = datefrom
            """
        )


def build_report_seed_bookings(room_ids, guest_ids):
    month_settings = [
        {
            "year": 2026,
            "month": 2,
            "max_start_day": 23,
        },
        {
            "year": 2026,
            "month": 3,
            "max_start_day": 26,
        },
        {
            "year": 2026,
            "month": 4,
            "max_start_day": 18,
        },
    ]

    bookings = []

    for index in range(REPORT_BOOKING_COUNT):
        month = month_settings[index % len(month_settings)]
        day = ((index * 7) % month["max_start_day"]) + 1
        nights = (index % 5) + 1
        datefrom = date(month["year"], month["month"], day)

        bookings.append(
            {
                "guest_id": guest_ids[index % len(guest_ids)],
                "room_id": room_ids[index % len(room_ids)],
                "datefrom": datefrom,
                "dateto": datefrom + timedelta(days=nights),
                "addinfo": f"{REPORT_BOOKING_PREFIX} {index + 1:03d}",
                "stars": (index % 5) + 1,
            }
        )

    return bookings


def insert_report_seed_bookings():
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT id
            FROM hotel_rooms
            ORDER BY room_number
            """
        )
        room_ids = [room["id"] for room in cur.fetchall()]

        cur.execute(
            """
            SELECT id
            FROM hotel_guests
            ORDER BY id
            """
        )
        guest_ids = [guest["id"] for guest in cur.fetchall()]

        if len(room_ids) == 0 or len(guest_ids) == 0:
            return

        for booking in build_report_seed_bookings(room_ids, guest_ids):
            cur.execute(
                """
                SELECT id
                FROM hotel_bookings
                WHERE addinfo = %(addinfo)s
                """,
                {
                    "addinfo": booking["addinfo"],
                },
            )

            if cur.fetchone() is not None:
                continue

            cur.execute(
                """
                INSERT INTO hotel_bookings (guest_id, room_id, datefrom, dateto, addinfo, stars)
                VALUES (%(guest_id)s, %(room_id)s, %(datefrom)s, %(dateto)s, %(addinfo)s, %(stars)s)
                """,
                booking,
            )


def create_monthly_report_view():
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("DROP VIEW IF EXISTS monthly_report")
        cur.execute(
            """
            CREATE VIEW monthly_report AS
            SELECT
                date_trunc('month', hotel_bookings.datefrom)::date AS month,
                COUNT(hotel_bookings.id)::int AS number_of_bookings,
                SUM(hotel_bookings.dateto - hotel_bookings.datefrom)::int AS number_of_nights,
                SUM((hotel_bookings.dateto - hotel_bookings.datefrom) * hotel_rooms.price)::numeric(10, 2) AS revenue
            FROM hotel_bookings
            INNER JOIN hotel_rooms ON hotel_rooms.id = hotel_bookings.room_id
            INNER JOIN hotel_guests ON hotel_guests.id = hotel_bookings.guest_id
            WHERE hotel_bookings.datefrom >= DATE '2026-02-01'
                AND hotel_bookings.datefrom < DATE '2026-05-01'
            GROUP BY date_trunc('month', hotel_bookings.datefrom)::date
            """
        )


def fetch_rooms():
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT id, room_number, type, price
            FROM hotel_rooms
            ORDER BY room_number
            """
        )
        rooms = cur.fetchall()

        for room in rooms:
            room["price"] = float(room["price"])
            room["room_type"] = room["type"]

        return rooms


def fetch_guests():
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT
                hotel_guests.id,
                hotel_guests.firstname,
                hotel_guests.lastname,
                hotel_guests.address,
                (
                    SELECT COUNT(*)
                    FROM hotel_bookings
                    WHERE hotel_bookings.guest_id = hotel_guests.id
                ) AS previous_visits
            FROM hotel_guests
            ORDER BY id
            """
        )
        return cur.fetchall()


def fetch_bookings(guest_id=None):
    with get_conn() as conn, conn.cursor() as cur:
        query = """
            SELECT
                hotel_bookings.id,
                hotel_bookings.guest_id,
                hotel_bookings.room_id,
                hotel_guests.firstname,
                hotel_guests.lastname,
                hotel_rooms.room_number,
                hotel_bookings.datefrom,
                hotel_bookings.dateto,
                hotel_bookings.addinfo,
                hotel_bookings.stars,
                (hotel_bookings.dateto - hotel_bookings.datefrom) AS number_of_nights,
                ((hotel_bookings.dateto - hotel_bookings.datefrom) * hotel_rooms.price) AS total_price
            FROM hotel_bookings
            INNER JOIN hotel_guests ON hotel_guests.id = hotel_bookings.guest_id
            INNER JOIN hotel_rooms ON hotel_rooms.id = hotel_bookings.room_id
        """
        params = {}

        if guest_id is not None:
            query += " WHERE hotel_bookings.guest_id = %(guest_id)s"
            params["guest_id"] = guest_id

        query += " ORDER BY hotel_bookings.datefrom, hotel_bookings.id"
        cur.execute(query, params)
        bookings = cur.fetchall()

        for booking in bookings:
            booking["guest_name"] = f'{booking["firstname"]} {booking["lastname"]}'
            booking["total_price"] = float(booking["total_price"])
            booking["nights"] = booking["number_of_nights"]

        return bookings


def fetch_monthly_report():
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT
                month,
                number_of_bookings,
                number_of_nights,
                revenue
            FROM monthly_report
            ORDER BY month
            """
        )
        report_rows = cur.fetchall()

        for row in report_rows:
            row["revenue"] = float(row["revenue"])

        return report_rows


def create_booking(room_id, booking_date, addinfo, guest_id=1, checkout_date=None):
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO hotel_bookings (guest_id, room_id, datefrom, dateto, addinfo)
            VALUES (%(guest_id)s, %(room_id)s, %(datefrom)s, %(dateto)s, %(addinfo)s)
            RETURNING id, guest_id, room_id, datefrom, dateto, addinfo, stars
            """,
            {
                "guest_id": guest_id,
                "room_id": room_id,
                "datefrom": booking_date,
                "dateto": checkout_date or (booking_date + timedelta(days=1)),
                "addinfo": addinfo,
            },
        )
        return cur.fetchone()


def update_booking_stars(booking_id, stars):
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
            UPDATE hotel_bookings
            SET stars = %(stars)s
            WHERE id = %(booking_id)s
            RETURNING id, guest_id, room_id, datefrom, dateto, addinfo, stars
            """,
            {
                "booking_id": booking_id,
                "stars": stars,
            },
        )
        return cur.fetchone()


def generate_random_game_code(length=8):
    alphabet = string.ascii_uppercase + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


def normalize_player_name(player_name):
    return player_name.strip()


def normalize_game_code(game_code):
    return game_code.strip().upper()


def assign_tasks_to_random_game(cur, game_id):
    cur.execute(
        """
        SELECT id, player_name, player_order, is_creator
        FROM random_game_players
        WHERE game_id = %(game_id)s
        ORDER BY player_order, id
        """,
        {
            "game_id": game_id,
        },
    )
    players = cur.fetchall()

    if len(players) != RANDOM_GAME_MAX_PLAYERS:
        return

    tasks = RANDOM_GAME_TASKS.copy()
    random.shuffle(tasks)

    for index, player in enumerate(players):
        cur.execute(
            """
            UPDATE random_game_players
            SET task_one = %(task_one)s,
                task_two = %(task_two)s
            WHERE id = %(player_id)s
            """,
            {
                "player_id": player["id"],
                "task_one": tasks[index * 2],
                "task_two": tasks[(index * 2) + 1],
            },
        )

    cur.execute(
        """
        UPDATE random_games
        SET status = 'ready'
        WHERE id = %(game_id)s
        """,
        {
            "game_id": game_id,
        },
    )


def create_random_game(creator_name):
    normalized_name = normalize_player_name(creator_name)

    if normalized_name == "":
        raise ValueError("Creator name is required")

    with get_conn() as conn:
        with conn.transaction():
            with conn.cursor() as cur:
                while True:
                    game_code = generate_random_game_code()
                    cur.execute(
                        """
                        SELECT id
                        FROM random_games
                        WHERE game_code = %(game_code)s
                        """,
                        {
                            "game_code": game_code,
                        },
                    )

                    if cur.fetchone() is None:
                        break

                cur.execute(
                    """
                    INSERT INTO random_games (game_code, max_players)
                    VALUES (%(game_code)s, %(max_players)s)
                    RETURNING id, game_code, status, max_players, created_at
                    """,
                    {
                        "game_code": game_code,
                        "max_players": RANDOM_GAME_MAX_PLAYERS,
                    },
                )
                game = cur.fetchone()

                cur.execute(
                    """
                    INSERT INTO random_game_players (game_id, player_name, player_order, is_creator)
                    VALUES (%(game_id)s, %(player_name)s, 1, TRUE)
                    RETURNING id
                    """,
                    {
                        "game_id": game["id"],
                        "player_name": normalized_name,
                    },
                )
                cur.fetchone()

                return fetch_random_game_by_code(game_code, cur=cur)


def join_random_game(game_code, player_name):
    normalized_game_code = normalize_game_code(game_code)
    normalized_name = normalize_player_name(player_name)

    if normalized_name == "":
        raise ValueError("Player name is required")

    with get_conn() as conn:
        with conn.transaction():
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, game_code, status, max_players, created_at
                    FROM random_games
                    WHERE game_code = %(game_code)s
                    FOR UPDATE
                    """,
                    {
                        "game_code": normalized_game_code,
                    },
                )
                game = cur.fetchone()

                if game is None:
                    raise LookupError("Game not found")

                cur.execute(
                    """
                    SELECT id, player_name
                    FROM random_game_players
                    WHERE game_id = %(game_id)s
                    ORDER BY player_order, id
                    """,
                    {
                        "game_id": game["id"],
                    },
                )
                players = cur.fetchall()

                for player in players:
                    if player["player_name"].casefold() == normalized_name.casefold():
                        raise ValueError("This name is already in the game")

                if len(players) >= game["max_players"]:
                    raise ValueError("This game is already full")

                cur.execute(
                    """
                    INSERT INTO random_game_players (game_id, player_name, player_order, is_creator)
                    VALUES (%(game_id)s, %(player_name)s, %(player_order)s, FALSE)
                    RETURNING id
                    """,
                    {
                        "game_id": game["id"],
                        "player_name": normalized_name,
                        "player_order": len(players) + 1,
                    },
                )
                cur.fetchone()

                if len(players) + 1 == game["max_players"]:
                    assign_tasks_to_random_game(cur, game["id"])

                return fetch_random_game_by_code(normalized_game_code, cur=cur)


def fetch_random_game_by_code(game_code, cur=None):
    normalized_game_code = normalize_game_code(game_code)
    should_close_connection = cur is None
    conn = None

    try:
        if cur is None:
            conn = get_conn()
            cur = conn.cursor()

        cur.execute(
            """
            SELECT id, game_code, status, max_players, created_at
            FROM random_games
            WHERE game_code = %(game_code)s
            """,
            {
                "game_code": normalized_game_code,
            },
        )
        game = cur.fetchone()

        if game is None:
            return None

        cur.execute(
            """
            SELECT
                id,
                player_name,
                player_order,
                is_creator,
                task_one,
                task_two,
                joined_at
            FROM random_game_players
            WHERE game_id = %(game_id)s
            ORDER BY player_order, id
            """,
            {
                "game_id": game["id"],
            },
        )
        players = cur.fetchall()

        return {
            "id": game["id"],
            "game_code": game["game_code"],
            "status": game["status"],
            "max_players": game["max_players"],
            "player_count": len(players),
            "share_path": f"/random-game/join/{game['game_code']}",
            "tasks": RANDOM_GAME_TASKS,
            "players": players,
        }
    finally:
        if should_close_connection and conn is not None:
            cur.close()
            conn.close()


def fetch_database_summary():
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) AS count FROM hotel_rooms")
        rooms_result = cur.fetchone()

        cur.execute("SELECT COUNT(*) AS count FROM hotel_guests")
        guests_result = cur.fetchone()

        cur.execute("SELECT COUNT(*) AS count FROM hotel_bookings")
        bookings_result = cur.fetchone()

        return {
            "room_count": rooms_result["count"],
            "guest_count": guests_result["count"],
            "booking_count": bookings_result["count"],
        }
