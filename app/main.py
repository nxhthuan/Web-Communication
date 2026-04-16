
from datetime import date
from typing import List

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from app.db import (
    create_booking,
    fetch_rooms,
    fetch_bookings,
    fetch_database_summary,
    fetch_guests,
    initialize_database,
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
    booking_date: date
    addinfo: str = ""


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
def get_bookings():
    return fetch_bookings()


@app.post("/bookings")
def post_booking(booking: BookingCreate):
    return create_booking(
        guest_id=booking.guest_id,
        room_id=booking.room_id,
        booking_date=booking.booking_date,
        addinfo=booking.addinfo,
    )


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
            }

            .column {
                width: 300px;
            }

            label, input, select {
                display: block;
                margin-bottom: 10px;
            }

            ul {
                padding-left: 20px;
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

                <section class="column">
                    <h2>Existing bookings</h2>
                    <ul id="booking-list"></ul>
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

            async function loadGuests() {
                const response = await fetch("/guests");
                const guests = await response.json();

                if (guests.length === 0) {
                    guestSelectElement.innerHTML = "<option>No guests</option>";
                    return;
                }

                guestSelectElement.innerHTML = guests.map((guest) => `
                    <option value="${guest.id}">
                        ${guest.firstname} ${guest.lastname} (${guest.previous_visits} visits)
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
                    <li>
                        ${booking.guest_name} - Room ${booking.room_number} -
                        ${formatDate(booking.datefrom)} -
                        ${booking.number_of_nights} night(s) -
                        ${booking.total_price} EUR
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
