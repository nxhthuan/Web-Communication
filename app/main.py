
import json
from datetime import date
from typing import List

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from app.db import (
    create_booking,
    create_random_game,
    fetch_rooms,
    fetch_bookings,
    fetch_database_summary,
    fetch_guests,
    fetch_monthly_report,
    fetch_random_game_by_code,
    initialize_database,
    join_random_game,
    update_booking_stars,
)

app = FastAPI()

origins = ["*"] # Change to the real front end origin in production

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

my_name = "Fredde"


class Room(BaseModel):
    id: int
    room_number: int
    type: str
    price: float


class BookingCreate(BaseModel):
    guest_id: int = 1
    room_id: int
    booking_date: date | None = None
    datefrom: date | None = None
    dateto: date | None = None
    addinfo: str = ""
    info: str = ""


class BookingStarsUpdate(BaseModel):
    stars: int = Field(ge=1, le=5)


class RandomGameCreateRequest(BaseModel):
    creator_name: str


class RandomGameJoinRequest(BaseModel):
    player_name: str


@app.on_event("startup")
def startup_event():
    initialize_database()

# Main route for this API
@app.get("/")
def read_root():
    summary = fetch_database_summary()

    return {
        "msg": "Hotel API!",
        "database": {
            "status": "connected",
            "room_count": summary["room_count"],
            "guest_count": summary["guest_count"],
            "booking_count": summary["booking_count"],
        },
    }


@app.get("/api/hello")
def api_hello():
    return {"msg": f"Hello {my_name}"}

# What is my ip 
@app.get("/api/ip")
def api_ip(request: Request): 
    # f-string concatenation
    return { "ip": request.client.host }

@app.get("/ip", response_class=HTMLResponse)
def html_ip(request: Request):
    return f"<h1>Your IP is {request.client.host}</h1>"


@app.get("/rooms", response_model=List[Room])
def get_rooms():
    return fetch_rooms()


@app.get("/guests")
def get_guests():
    return fetch_guests()


@app.get("/bookings")
def get_bookings(guest_id: int | None = None):
    return fetch_bookings(guest_id=guest_id)


@app.get("/monthly-report")
def get_monthly_report():
    return fetch_monthly_report()


@app.get("/monthly-report-page", response_class=HTMLResponse)
def monthly_report_page():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
        <title>Monthly Report</title>
    </head>
    <body>
        <h3>Monthly report</h3>

        <table border="1">
            <thead>
                <tr>
                    <th>Month</th>
                    <th>Bookings</th>
                    <th>Nights</th>
                    <th>Revenue</th>
                </tr>
            </thead>
            <tbody id="monthly-report-list"></tbody>
        </table>

        <script>
            async function getMonthlyReport() {
                const res = await fetch("/monthly-report");
                const reportRows = await res.json();

                document.getElementById("monthly-report-list").innerHTML = "";

                for (r of reportRows) {
                    document.getElementById("monthly-report-list").innerHTML += `
                        <tr>
                            <td>${r.month}</td>
                            <td>${r.number_of_bookings}</td>
                            <td>${r.number_of_nights}</td>
                            <td>${r.revenue} EUR</td>
                        </tr>
                    `;
                }
            }

            getMonthlyReport();
        </script>
    </body>
    </html>
    """


@app.post("/bookings")
def post_booking(booking: BookingCreate):
    booking_date = booking.booking_date or booking.datefrom

    if booking_date is None:
        raise HTTPException(status_code=422, detail="booking_date or datefrom is required")

    if booking.dateto is not None and booking.dateto <= booking_date:
        raise HTTPException(status_code=422, detail="dateto must be after booking_date")

    addinfo = booking.addinfo or booking.info

    return create_booking(
        guest_id=booking.guest_id,
        room_id=booking.room_id,
        booking_date=booking_date,
        checkout_date=booking.dateto,
        addinfo=addinfo,
    )


@app.put("/bookings/{booking_id}")
def put_booking_stars(booking_id: int, booking_update: BookingStarsUpdate):
    updated_booking = update_booking_stars(booking_id=booking_id, stars=booking_update.stars)

    if updated_booking is None:
        raise HTTPException(status_code=404, detail="Booking not found")

    return updated_booking


@app.post("/api/random-games")
def post_random_game(game_request: RandomGameCreateRequest):
    try:
        return create_random_game(game_request.creator_name)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.get("/api/random-games/{game_code}")
def get_random_game(game_code: str):
    game = fetch_random_game_by_code(game_code)

    if game is None:
        raise HTTPException(status_code=404, detail="Game not found")

    return game


@app.post("/api/random-games/{game_code}/join")
def post_random_game_join(game_code: str, join_request: RandomGameJoinRequest):
    try:
        return join_random_game(game_code, join_request.player_name)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.get("/rooms-page", response_class=HTMLResponse)
def rooms_page():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
        <title>Dashboard</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                margin: 24px;
            }

            .layout {
                display: flex;
                gap: 40px;
                align-items: flex-start;
                flex-wrap: wrap;
            }

            .column {
                width: 300px;
            }

            .booking-column {
                width: 560px;
            }

            label, input, select {
                display: block;
                margin-bottom: 10px;
            }

            ul {
                padding-left: 0;
                list-style: none;
                margin: 0;
            }

            .booking-list-box {
                border: 1px solid #ccc;
                padding: 10px 12px;
            }

            .booking-item p {
                margin: 2px 0;
            }

            .booking-item {
                padding: 8px 0;
            }

        </style>
    </head>
    <body>
        <main>
            <h1>Booking dashboard</h1>

            <div class="layout">
                <section class="column">
                    <h2>Book a room</h2>

                    <label for="guest-select">Choose guest</label>
                    <select id="guest-select"></select>

                    <label for="room-select">Choose room</label>
                    <select id="room-select"></select>

                    <label for="bed-type">Bed option</label>
                    <select id="bed-type">
                        <option value="King bed">King bed</option>
                        <option value="Twin room">Twin room</option>
                    </select>

                    <label for="booking-date">Booking date</label>
                    <input type="date" id="booking-date" />

                    <label for="addinfo">Additional information</label>
                    <input type="text" id="addinfo" placeholder="Guest request" />

                    <input type="button" id="save-button" value="Save booking" />

                    <p id="message"></p>
                </section>

                <section class="column booking-column">
                    <h2>Existing bookings</h2>
                    <div class="booking-list-box">
                        <ul id="booking-list"></ul>
                    </div>
                </section>
            </div>
        </main>

        <script>
            const guestSelectElement = document.getElementById("guest-select");
            const roomSelectElement = document.getElementById("room-select");
            const bedTypeElement = document.getElementById("bed-type");
            const bookingDateElement = document.getElementById("booking-date");
            const addinfoElement = document.getElementById("addinfo");
            const saveButtonElement = document.getElementById("save-button");
            const messageElement = document.getElementById("message");
            const bookingListElement = document.getElementById("booking-list");

            function formatDate(dateString) {
                const parts = dateString.split("-");

                if (parts.length !== 3) {
                    return dateString;
                }

                return parts[2] + "/" + parts[1] + "/" + parts[0];
            }

            function splitBookingInfo(addinfo) {
                if (!addinfo) {
                    return {
                        bedOption: "-",
                        additionalInformation: "-"
                    };
                }

                const normalizedAddinfo = addinfo.trim();
                const knownBedOptions = ["King bed", "Twin room", "king bed", "twin room"];

                if (knownBedOptions.includes(normalizedAddinfo)) {
                    return {
                        bedOption: normalizedAddinfo,
                        additionalInformation: "-"
                    };
                }

                const parts = normalizedAddinfo.split(" - ");

                if (parts.length === 1) {
                    return {
                        bedOption: "-",
                        additionalInformation: normalizedAddinfo
                    };
                }

                return {
                    bedOption: parts[0],
                    additionalInformation: parts.slice(1).join(" - ")
                };
            }

            async function loadGuests() {
                const response = await fetch("/guests");
                const guests = await response.json();

                if (guests.length === 0) {
                    guestSelectElement.innerHTML = "<option>No guests</option>";
                    return;
                }

                guestSelectElement.innerHTML = guests.map((guest) => `
                    <option value="${guest.id}">
                        ${guest.firstname} ${guest.lastname}
                    </option>
                `).join("");
            }

            async function loadRooms() {
                const response = await fetch("/rooms");
                const rooms = await response.json();

                if (rooms.length === 0) {
                    roomSelectElement.innerHTML = "<option>No rooms</option>";
                    return;
                }

                roomSelectElement.innerHTML = rooms.map((room) => `
                    <option value="${room.id}">
                        Room ${room.room_number} - ${room.type}
                    </option>
                `).join("");
            }

            async function loadBookings() {
                const response = await fetch("/bookings");
                const bookings = await response.json();

                if (bookings.length === 0) {
                    bookingListElement.innerHTML = "<li>No bookings yet.</li>";
                    return;
                }

                bookingListElement.innerHTML = bookings.map((booking) => `
                    <li class="booking-item">
                        <p><strong>Guest:</strong> ${booking.guest_name} | <strong>Room:</strong> ${booking.room_number} | <strong>Date:</strong> ${formatDate(booking.datefrom)}</p>
                        <p><strong>Bed option:</strong> ${splitBookingInfo(booking.addinfo).bedOption} | <strong>Nights:</strong> ${booking.number_of_nights} | <strong>Total price:</strong> ${booking.total_price} EUR</p>
                        <p><strong>Additional information:</strong> ${splitBookingInfo(booking.addinfo).additionalInformation}</p>
                    </li>
                `).join("");
            }

            async function saveBooking() {
                messageElement.textContent = "";

                if (!bookingDateElement.value) {
                    messageElement.textContent = "Please choose a date.";
                    return;
                }

                const extraInfo = addinfoElement.value.trim();
                const fullAddinfo = extraInfo
                    ? bedTypeElement.value + " - " + extraInfo
                    : bedTypeElement.value;

                const body = {
                    guest_id: Number(guestSelectElement.value),
                    room_id: Number(roomSelectElement.value),
                    booking_date: bookingDateElement.value,
                    addinfo: fullAddinfo
                };

                const response = await fetch("/bookings", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify(body)
                });

                if (!response.ok) {
                    messageElement.textContent = "Could not save booking.";
                    return;
                }

                messageElement.textContent = "Booking saved.";
                bookingDateElement.value = "";
                addinfoElement.value = "";
                await loadBookings();
            }

            saveButtonElement.addEventListener("click", saveBooking);
            loadGuests();
            loadRooms();
            loadBookings();
        </script>
    </body>
    </html>
    """


@app.get("/guest-page", response_class=HTMLResponse)
def guest_page():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
        <title>Guest Reviews</title>
    </head>
    <body>
        <h3>Guest dashboard</h3>

        Guest:
        <select id="guest-list"></select>
        <br><br>

        <p id="message"></p>

        <h3>Bookings:</h3>
        <ul id="bookings-list"></ul>

        <script>
            const guestListElement = document.getElementById("guest-list");
            const bookingsListElement = document.getElementById("bookings-list");
            const messageElement = document.getElementById("message");

            function formatDate(dateString) {
                const parts = dateString.split("-");

                if (parts.length !== 3) {
                    return dateString;
                }

                return parts[2] + "/" + parts[1] + "/" + parts[0];
            }

            function splitBookingInfo(addinfo) {
                if (!addinfo) {
                    return {
                        bedOption: "-",
                        additionalInformation: "-"
                    };
                }

                const normalizedAddinfo = addinfo.trim();
                const parts = normalizedAddinfo.split(" - ");

                if (parts.length === 1) {
                    return {
                        bedOption: "-",
                        additionalInformation: normalizedAddinfo
                    };
                }

                return {
                    bedOption: parts[0],
                    additionalInformation: parts.slice(1).join(" - ")
                };
            }

            async function getGuests() {
                const response = await fetch("/guests");
                const guests = await response.json();

                if (guests.length === 0) {
                    guestListElement.innerHTML = "<option>No guests</option>";
                    bookingsListElement.innerHTML = "<li>No guests found.</li>";
                    return;
                }

                guestListElement.innerHTML = guests.map((guest) => `
                    <option value="${guest.id}">
                        ${guest.firstname} ${guest.lastname}
                    </option>
                `).join("");

                await getBookings();
            }

            async function saveStars(bookingId, stars) {
                const response = await fetch("/bookings/" + bookingId, {
                    method: "PUT",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify({
                        stars: Number(stars)
                    })
                });

                if (!response.ok) {
                    messageElement.textContent = "Could not save review.";
                    return;
                }

                messageElement.textContent = "Review saved.";
                await getBookings();
            }

            async function getBookings() {
                const guestId = guestListElement.value;

                if (!guestId) {
                    bookingsListElement.innerHTML = "<li>Choose a guest.</li>";
                    return;
                }

                const response = await fetch("/bookings?guest_id=" + guestId);
                const bookings = await response.json();

                if (bookings.length === 0) {
                    bookingsListElement.innerHTML = "<li>This guest has no bookings yet.</li>";
                    return;
                }

                bookingsListElement.innerHTML = bookings.map((booking) => `
                    <li>
                        <strong>Guest:</strong> ${booking.guest_name}
                        | <strong>Room:</strong> ${booking.room_number}
                        | <strong>Check-in:</strong> ${formatDate(booking.datefrom)}
                        | <strong>Check-out:</strong> ${formatDate(booking.dateto)}
                        <br>
                        <strong>Bed option:</strong> ${splitBookingInfo(booking.addinfo).bedOption}
                        | <strong>Nights:</strong> ${booking.number_of_nights}
                        | <strong>Total price:</strong> ${booking.total_price} EUR
                        <br>
                        <strong>Review:</strong>
                        <select id="stars-${booking.id}" onchange="saveStars(${booking.id}, this.value)">
                            <option value="1" ${(booking.stars ?? 1) === 1 ? "selected" : ""}>⭐</option>
                            <option value="2" ${booking.stars === 2 ? "selected" : ""}>⭐⭐</option>
                            <option value="3" ${booking.stars === 3 ? "selected" : ""}>⭐⭐⭐</option>
                            <option value="4" ${booking.stars === 4 ? "selected" : ""}>⭐⭐⭐⭐</option>
                            <option value="5" ${booking.stars === 5 ? "selected" : ""}>⭐⭐⭐⭐⭐</option>
                        </select>
                        <br><br>
                    </li>
                `).join("");
            }

            guestListElement.addEventListener("change", getBookings);
            getGuests();
        </script>
    </body>
    </html>
    """


@app.get("/random-game/create", response_class=HTMLResponse)
def random_game_create_page():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
        <title>Create Random Game</title>
        <style>
            :root {
                color-scheme: light;
                --bg: #f6efe5;
                --panel: #fffaf4;
                --text: #1f2937;
                --accent: #d97706;
                --accent-dark: #9a3412;
                --muted: #6b7280;
                --line: #ead7c3;
            }

            * {
                box-sizing: border-box;
            }

            body {
                margin: 0;
                min-height: 100vh;
                font-family: Georgia, "Times New Roman", serif;
                color: var(--text);
                background:
                    radial-gradient(circle at top left, rgba(245, 158, 11, 0.22), transparent 30%),
                    linear-gradient(135deg, #f9f2e8 0%, #f3e5d2 100%);
            }

            main {
                max-width: 960px;
                margin: 0 auto;
                padding: 48px 20px;
            }

            .hero {
                display: grid;
                grid-template-columns: 1.2fr 0.8fr;
                gap: 24px;
                align-items: stretch;
            }

            .panel {
                background: var(--panel);
                border: 1px solid var(--line);
                border-radius: 24px;
                padding: 24px;
                box-shadow: 0 20px 45px rgba(154, 52, 18, 0.08);
            }

            h1, h2 {
                margin-top: 0;
            }

            p {
                line-height: 1.6;
            }

            label {
                display: block;
                margin-bottom: 8px;
                font-weight: 700;
            }

            input, button {
                width: 100%;
                padding: 14px 16px;
                border-radius: 14px;
                border: 1px solid #d6c1ab;
                font: inherit;
            }

            button {
                margin-top: 14px;
                border: 0;
                cursor: pointer;
                color: white;
                background: linear-gradient(135deg, var(--accent) 0%, var(--accent-dark) 100%);
            }

            button:disabled {
                cursor: wait;
                opacity: 0.7;
            }

            .task-grid {
                display: grid;
                grid-template-columns: repeat(2, minmax(0, 1fr));
                gap: 10px;
                padding: 0;
                list-style: none;
            }

            .task-grid li {
                padding: 10px 12px;
                border-radius: 12px;
                background: #fff;
                border: 1px solid var(--line);
            }

            .note, #message {
                color: var(--muted);
            }

            @media (max-width: 760px) {
                .hero {
                    grid-template-columns: 1fr;
                }
            }
        </style>
    </head>
    <body>
        <main>
            <div class="hero">
                <section class="panel">
                    <h1>Create a 6-player random game</h1>
                    <p>
                        The host enters a name first. After the game is created, the app generates
                        an invite link to share with the other 5 players.
                    </p>

                    <label for="creator-name">Host name</label>
                    <input id="creator-name" type="text" placeholder="Example: Tony" maxlength="100" />

                    <button id="create-game-button">Create game</button>
                    <p id="message"></p>
                </section>

                <aside class="panel">
                    <h2>Task list</h2>
                    <p class="note">The 12 tasks will be shuffled into 6 pairs, and each player gets 2 different tasks.</p>
                    <ol class="task-grid">
                        <li>Heading 1</li>
                        <li>Heading 2</li>
                        <li>Heading 3</li>
                        <li>Heading 4</li>
                        <li>Heading 5</li>
                        <li>Heading 6</li>
                        <li>Heading 7</li>
                        <li>Heading 8</li>
                        <li>Heading 9</li>
                        <li>Heading 10</li>
                        <li>Heading 11</li>
                        <li>Heading 12</li>
                    </ol>
                </aside>
            </div>
        </main>

        <script>
            const creatorNameElement = document.getElementById("creator-name");
            const createGameButtonElement = document.getElementById("create-game-button");
            const messageElement = document.getElementById("message");

            async function createGame() {
                const creatorName = creatorNameElement.value.trim();

                if (!creatorName) {
                    messageElement.textContent = "Please enter the host name.";
                    return;
                }

                createGameButtonElement.disabled = true;
                messageElement.textContent = "Creating game...";

                const response = await fetch("/api/random-games", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify({
                        creator_name: creatorName
                    })
                });

                const payload = await response.json();

                if (!response.ok) {
                    messageElement.textContent = payload.detail || "Could not create the game.";
                    createGameButtonElement.disabled = false;
                    return;
                }

                window.location.href = "/random-game/host/" + payload.game_code + "?player=" + encodeURIComponent(creatorName);
            }

            createGameButtonElement.addEventListener("click", createGame);
            creatorNameElement.addEventListener("keydown", (event) => {
                if (event.key === "Enter") {
                    createGame();
                }
            });
        </script>
    </body>
    </html>
    """


def build_random_game_host_page(game_code: str):
    template = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
        <title>Host Random Game</title>
        <style>
            :root {
                color-scheme: light;
                --bg: #f3efe7;
                --panel: rgba(255, 252, 247, 0.95);
                --text: #1f2937;
                --muted: #6b7280;
                --line: #e5d3bd;
                --accent: #0f766e;
                --accent-strong: #115e59;
                --soft: #eef8f6;
                --highlight: #fff4d8;
            }

            * {
                box-sizing: border-box;
            }

            body {
                margin: 0;
                min-height: 100vh;
                color: var(--text);
                font-family: "Trebuchet MS", "Segoe UI", sans-serif;
                background:
                    radial-gradient(circle at top right, rgba(20, 184, 166, 0.2), transparent 28%),
                    radial-gradient(circle at bottom left, rgba(245, 158, 11, 0.16), transparent 22%),
                    var(--bg);
            }

            main {
                max-width: 1100px;
                margin: 0 auto;
                padding: 32px 20px 48px;
            }

            .page-header {
                margin-bottom: 20px;
            }

            .layout {
                display: grid;
                grid-template-columns: 1.1fr 0.9fr;
                gap: 20px;
            }

            .panel {
                background: var(--panel);
                border: 1px solid var(--line);
                border-radius: 22px;
                padding: 20px;
                box-shadow: 0 18px 40px rgba(15, 118, 110, 0.08);
            }

            .row {
                display: flex;
                gap: 10px;
                align-items: center;
                flex-wrap: wrap;
            }

            input, button {
                padding: 12px 14px;
                border-radius: 12px;
                border: 1px solid #cbd5d1;
                font: inherit;
            }

            input {
                flex: 1;
                min-width: 240px;
                background: white;
            }

            button {
                border: 0;
                cursor: pointer;
                color: white;
                background: linear-gradient(135deg, var(--accent) 0%, var(--accent-strong) 100%);
            }

            .status-pill {
                display: inline-flex;
                align-items: center;
                gap: 8px;
                padding: 8px 12px;
                border-radius: 999px;
                background: var(--soft);
                color: var(--accent-strong);
                font-weight: 700;
            }

            ul, ol {
                margin: 0;
                padding-left: 20px;
            }

            .player-list li {
                margin-bottom: 10px;
            }

            .assignment-grid {
                display: grid;
                grid-template-columns: repeat(2, minmax(0, 1fr));
                gap: 12px;
                margin-top: 16px;
            }

            .assignment-card {
                border: 1px solid var(--line);
                border-radius: 16px;
                padding: 14px;
                background: white;
            }

            .assignment-card.current-player {
                background: var(--highlight);
                border-color: #f59e0b;
            }

            .task-pair {
                margin-top: 8px;
                color: var(--muted);
            }

            .muted {
                color: var(--muted);
            }

            @media (max-width: 860px) {
                .layout {
                    grid-template-columns: 1fr;
                }

                .assignment-grid {
                    grid-template-columns: 1fr;
                }
            }
        </style>
    </head>
    <body>
        <main>
            <header class="page-header">
                <h1>Game host room</h1>
                <p class="muted">Share the link below with 5 other people. Once 6 players have joined, tasks are assigned automatically.</p>
            </header>

            <div class="layout">
                <section class="panel">
                    <div class="row" style="justify-content: space-between; margin-bottom: 16px;">
                        <div>
                            <div class="status-pill" id="status-pill">Loading...</div>
                        </div>
                        <div><strong>Game code:</strong> <span id="game-code-label"></span></div>
                    </div>

                    <h2>Share link</h2>
                    <div class="row">
                        <input id="share-link" type="text" readonly />
                        <button id="copy-link-button" type="button">Copy link</button>
                    </div>

                    <p id="host-message" class="muted"></p>

                    <h2>Players</h2>
                    <ul id="players-list" class="player-list"></ul>
                </section>

                <aside class="panel">
                    <h2>Task list</h2>
                    <ol id="task-list"></ol>

                    <div id="result-block" style="margin-top: 22px;">
                        <h2>Random results</h2>
                        <p id="result-message" class="muted">Waiting for all players to join.</p>
                        <div id="assignment-grid" class="assignment-grid"></div>
                    </div>
                </aside>
            </div>
        </main>

        <script>
            const gameCode = __GAME_CODE__;
            const statusPillElement = document.getElementById("status-pill");
            const gameCodeLabelElement = document.getElementById("game-code-label");
            const shareLinkElement = document.getElementById("share-link");
            const copyLinkButtonElement = document.getElementById("copy-link-button");
            const hostMessageElement = document.getElementById("host-message");
            const playersListElement = document.getElementById("players-list");
            const taskListElement = document.getElementById("task-list");
            const resultMessageElement = document.getElementById("result-message");
            const assignmentGridElement = document.getElementById("assignment-grid");

            const rememberedPlayerName = new URLSearchParams(window.location.search).get("player");

            function escapeHtml(value) {
                return String(value)
                    .replaceAll("&", "&amp;")
                    .replaceAll("<", "&lt;")
                    .replaceAll(">", "&gt;")
                    .replaceAll('"', "&quot;")
                    .replaceAll("'", "&#39;");
            }

            function renderPlayers(players) {
                playersListElement.innerHTML = players.map((player) => `
                    <li>
                        <strong>${escapeHtml(player.player_name)}</strong>
                        ${player.is_creator ? "<span>(creator)</span>" : ""}
                    </li>
                `).join("");
            }

            function renderAssignments(players) {
                assignmentGridElement.innerHTML = players.map((player) => {
                    const currentClass = rememberedPlayerName && player.player_name.toLowerCase() === rememberedPlayerName.toLowerCase()
                        ? "assignment-card current-player"
                        : "assignment-card";

                    return `
                        <article class="${currentClass}">
                            <strong>${escapeHtml(player.player_name)}</strong>
                            <div class="task-pair">${escapeHtml(player.task_one || "-")} + ${escapeHtml(player.task_two || "-")}</div>
                        </article>
                    `;
                }).join("");
            }

            async function loadGame() {
                const response = await fetch("/api/random-games/" + gameCode);

                if (!response.ok) {
                    statusPillElement.textContent = "Game not found";
                    hostMessageElement.textContent = "Game not found.";
                    return;
                }

                const game = await response.json();
                const shareUrl = window.location.origin + game.share_path;
                const playersNeeded = Math.max(game.max_players - game.player_count, 0);

                gameCodeLabelElement.textContent = game.game_code;
                shareLinkElement.value = shareUrl;
                taskListElement.innerHTML = game.tasks.map((task) => `<li>${escapeHtml(task)}</li>`).join("");
                renderPlayers(game.players);

                if (game.status === "ready") {
                    statusPillElement.textContent = "Ready: 6/6 players";
                    resultMessageElement.textContent = "Each player has been assigned 2 different tasks.";
                    renderAssignments(game.players);
                } else {
                    statusPillElement.textContent = "Waiting: " + game.player_count + "/" + game.max_players + " players";
                    resultMessageElement.textContent = playersNeeded + " more player(s) needed before the random assignment starts.";
                    assignmentGridElement.innerHTML = "";
                }
            }

            copyLinkButtonElement.addEventListener("click", async () => {
                await navigator.clipboard.writeText(shareLinkElement.value);
                hostMessageElement.textContent = "Invite link copied.";
            });

            loadGame();
            setInterval(loadGame, 3000);
        </script>
    </body>
    </html>
    """

    return template.replace("__GAME_CODE__", json.dumps(game_code))


def build_random_game_join_page(game_code: str):
    template = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
        <title>Join Random Game</title>
        <style>
            :root {
                color-scheme: light;
                --bg: #eef5f1;
                --panel: rgba(255, 255, 255, 0.94);
                --text: #1f2937;
                --muted: #6b7280;
                --line: #cfe2d8;
                --accent: #2563eb;
                --accent-strong: #1d4ed8;
                --success: #166534;
                --spotlight: #dbeafe;
            }

            * {
                box-sizing: border-box;
            }

            body {
                margin: 0;
                min-height: 100vh;
                color: var(--text);
                font-family: Verdana, Geneva, sans-serif;
                background:
                    radial-gradient(circle at top center, rgba(37, 99, 235, 0.18), transparent 26%),
                    linear-gradient(180deg, #edf6ff 0%, var(--bg) 100%);
            }

            main {
                max-width: 980px;
                margin: 0 auto;
                padding: 32px 20px 48px;
            }

            .layout {
                display: grid;
                grid-template-columns: 0.95fr 1.05fr;
                gap: 20px;
            }

            .panel {
                background: var(--panel);
                border-radius: 22px;
                border: 1px solid var(--line);
                padding: 20px;
                box-shadow: 0 18px 42px rgba(37, 99, 235, 0.08);
            }

            input, button {
                width: 100%;
                padding: 13px 14px;
                border-radius: 12px;
                border: 1px solid #cbd5e1;
                font: inherit;
            }

            button {
                border: 0;
                cursor: pointer;
                color: white;
                background: linear-gradient(135deg, var(--accent) 0%, var(--accent-strong) 100%);
                margin-top: 12px;
            }

            ul, ol {
                margin: 0;
                padding-left: 20px;
            }

            .player-list li {
                margin-bottom: 10px;
            }

            .assignment-grid {
                display: grid;
                grid-template-columns: repeat(2, minmax(0, 1fr));
                gap: 12px;
                margin-top: 16px;
            }

            .assignment-card {
                border: 1px solid var(--line);
                border-radius: 16px;
                padding: 14px;
                background: white;
            }

            .assignment-card.current-player {
                background: var(--spotlight);
                border-color: #60a5fa;
            }

            .success {
                color: var(--success);
            }

            .muted {
                color: var(--muted);
            }

            @media (max-width: 860px) {
                .layout {
                    grid-template-columns: 1fr;
                }

                .assignment-grid {
                    grid-template-columns: 1fr;
                }
            }
        </style>
    </head>
    <body>
        <main>
            <header style="margin-bottom: 20px;">
                <h1>Join random task game</h1>
                <p class="muted">Enter your name to join the game. When 6 players are in, the app assigns tasks to everyone.</p>
            </header>

            <div class="layout">
                <section class="panel">
                    <h2>Join game</h2>
                    <p><strong>Game code:</strong> <span id="game-code-label"></span></p>
                    <div id="join-form-block">
                        <input id="player-name" type="text" placeholder="Enter your name" maxlength="100" />
                        <button id="join-button" type="button">Join game</button>
                    </div>
                    <p id="join-message" class="muted"></p>

                    <h2>Players</h2>
                    <ul id="players-list" class="player-list"></ul>
                </section>

                <aside class="panel">
                    <h2>Task list</h2>
                    <ol id="task-list"></ol>

                    <div style="margin-top: 22px;">
                        <h2>Random results</h2>
                        <p id="result-message" class="muted">Waiting for 6 players to join.</p>
                        <div id="assignment-grid" class="assignment-grid"></div>
                    </div>
                </aside>
            </div>
        </main>

        <script>
            const gameCode = __GAME_CODE__;
            const storageKey = "random-game-player-" + gameCode;
            const params = new URLSearchParams(window.location.search);
            const queryPlayerName = params.get("player");

            const gameCodeLabelElement = document.getElementById("game-code-label");
            const joinFormBlockElement = document.getElementById("join-form-block");
            const playerNameElement = document.getElementById("player-name");
            const joinButtonElement = document.getElementById("join-button");
            const joinMessageElement = document.getElementById("join-message");
            const playersListElement = document.getElementById("players-list");
            const taskListElement = document.getElementById("task-list");
            const resultMessageElement = document.getElementById("result-message");
            const assignmentGridElement = document.getElementById("assignment-grid");

            let rememberedPlayerName = queryPlayerName || sessionStorage.getItem(storageKey) || "";

            function escapeHtml(value) {
                return String(value)
                    .replaceAll("&", "&amp;")
                    .replaceAll("<", "&lt;")
                    .replaceAll(">", "&gt;")
                    .replaceAll('"', "&quot;")
                    .replaceAll("'", "&#39;");
            }

            function persistPlayerName(name) {
                rememberedPlayerName = name;
                sessionStorage.setItem(storageKey, name);

                const nextParams = new URLSearchParams(window.location.search);
                nextParams.set("player", name);
                window.history.replaceState({}, "", window.location.pathname + "?" + nextParams.toString());
            }

            function renderPlayers(players) {
                playersListElement.innerHTML = players.map((player) => `
                    <li>
                        <strong>${escapeHtml(player.player_name)}</strong>
                        ${player.is_creator ? "<span>(creator)</span>" : ""}
                    </li>
                `).join("");
            }

            function renderAssignments(players) {
                assignmentGridElement.innerHTML = players.map((player) => {
                    const currentClass = rememberedPlayerName && player.player_name.toLowerCase() === rememberedPlayerName.toLowerCase()
                        ? "assignment-card current-player"
                        : "assignment-card";

                    return `
                        <article class="${currentClass}">
                            <strong>${escapeHtml(player.player_name)}</strong>
                            <div style="margin-top: 8px;" class="${currentClass.includes("current-player") ? "success" : "muted"}">
                                ${escapeHtml(player.task_one || "-")} + ${escapeHtml(player.task_two || "-")}
                            </div>
                        </article>
                    `;
                }).join("");
            }

            async function loadGame() {
                const response = await fetch("/api/random-games/" + gameCode);

                if (!response.ok) {
                    joinMessageElement.textContent = "Game not found.";
                    joinFormBlockElement.style.display = "none";
                    return;
                }

                const game = await response.json();
                const joinedPlayer = game.players.find((player) =>
                    rememberedPlayerName && player.player_name.toLowerCase() === rememberedPlayerName.toLowerCase()
                );

                gameCodeLabelElement.textContent = game.game_code;
                taskListElement.innerHTML = game.tasks.map((task) => `<li>${escapeHtml(task)}</li>`).join("");
                renderPlayers(game.players);

                if (joinedPlayer) {
                    joinFormBlockElement.style.display = "none";
                    joinMessageElement.textContent = "You joined this game as: " + joinedPlayer.player_name;
                    joinMessageElement.className = "success";
                } else if (game.player_count >= game.max_players) {
                    joinFormBlockElement.style.display = "none";
                    joinMessageElement.textContent = "This game is already full.";
                    joinMessageElement.className = "muted";
                } else {
                    joinFormBlockElement.style.display = "block";
                    joinMessageElement.className = "muted";
                }

                if (game.status === "ready") {
                    resultMessageElement.textContent = "Task assignment is complete. Each player has 2 different tasks.";
                    renderAssignments(game.players);
                } else {
                    resultMessageElement.textContent = "Current players: " + game.player_count + "/" + game.max_players + ".";
                    assignmentGridElement.innerHTML = "";
                }
            }

            async function joinGame() {
                const playerName = playerNameElement.value.trim();

                if (!playerName) {
                    joinMessageElement.textContent = "Please enter your name.";
                    joinMessageElement.className = "muted";
                    return;
                }

                joinButtonElement.disabled = true;
                joinMessageElement.textContent = "Joining game...";
                joinMessageElement.className = "muted";

                const response = await fetch("/api/random-games/" + gameCode + "/join", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify({
                        player_name: playerName
                    })
                });

                const payload = await response.json();
                joinButtonElement.disabled = false;

                if (!response.ok) {
                    joinMessageElement.textContent = payload.detail || "Could not join the game.";
                    return;
                }

                persistPlayerName(playerName);
                playerNameElement.value = "";
                joinMessageElement.textContent = "Joined successfully.";
                joinMessageElement.className = "success";
                await loadGame();
            }

            joinButtonElement.addEventListener("click", joinGame);
            playerNameElement.addEventListener("keydown", (event) => {
                if (event.key === "Enter") {
                    joinGame();
                }
            });

            loadGame();
            setInterval(loadGame, 3000);
        </script>
    </body>
    </html>
    """

    return template.replace("__GAME_CODE__", json.dumps(game_code))


@app.get("/random-game/host/{game_code}", response_class=HTMLResponse)
def random_game_host_page(game_code: str):
    return build_random_game_host_page(game_code)


@app.get("/random-game/join/{game_code}", response_class=HTMLResponse)
def random_game_join_page(game_code: str):
    return build_random_game_join_page(game_code)
