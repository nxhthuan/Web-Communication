import os
from datetime import timedelta

import psycopg

DATABASE_URL = os.getenv("DATABASE_URL")

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
        "firstname": "Tony",
        "lastname": "Nguyen",
        "address": "Arcada, Helsinki",
    },
    {
        "firstname": "Emma",
        "lastname": "Virtanen",
        "address": "Espoo, Finland",
    },
]

BOOKING_SEED_DATA = [
    {
        "guest_id": 1,
        "room_id": 1,
        "datefrom": "2026-04-10",
        "dateto": "2026-04-12",
        "addinfo": "Late check-in",
    },
    {
        "guest_id": 2,
        "room_id": 2,
        "datefrom": "2026-04-15",
        "dateto": "2026-04-18",
        "addinfo": "Needs baby crib",
    },
]


def get_conn():
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL is not set")
    return psycopg.connect(DATABASE_URL, autocommit=True, row_factory=psycopg.rows.dict_row)


def initialize_database():
    create_tables()
    insert_sample_rooms()
    insert_sample_guests()
    insert_sample_bookings()


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


def fetch_bookings():
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
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
                (hotel_bookings.dateto - hotel_bookings.datefrom) AS number_of_nights,
                ((hotel_bookings.dateto - hotel_bookings.datefrom) * hotel_rooms.price) AS total_price
            FROM hotel_bookings
            INNER JOIN hotel_guests ON hotel_guests.id = hotel_bookings.guest_id
            INNER JOIN hotel_rooms ON hotel_rooms.id = hotel_bookings.room_id
            ORDER BY hotel_bookings.datefrom, hotel_bookings.id
            """
        )
        bookings = cur.fetchall()

        for booking in bookings:
            booking["guest_name"] = f'{booking["firstname"]} {booking["lastname"]}'
            booking["total_price"] = float(booking["total_price"])

        return bookings


def create_booking(room_id, booking_date, addinfo, guest_id=1):
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO hotel_bookings (guest_id, room_id, datefrom, dateto, addinfo)
            VALUES (%(guest_id)s, %(room_id)s, %(datefrom)s, %(dateto)s, %(addinfo)s)
            RETURNING id, guest_id, room_id, datefrom, dateto, addinfo
            """,
            {
                "guest_id": guest_id,
                "room_id": room_id,
                "datefrom": booking_date,
                "dateto": booking_date + timedelta(days=1),
                "addinfo": addinfo,
            },
        )
        return cur.fetchone()


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
