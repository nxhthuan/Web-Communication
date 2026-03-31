
from typing import List

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

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
    room_number: str
    room_type: str
    floor: int
    price_per_night: int
    max_guests: int
    is_bookable: bool


rooms_data = [
    {
        "room_number": "101",
        "room_type": "Single",
        "floor": 1,
        "price_per_night": 75,
        "max_guests": 1,
        "is_bookable": True,
    },
    {
        "room_number": "203",
        "room_type": "Double",
        "floor": 2,
        "price_per_night": 110,
        "max_guests": 2,
        "is_bookable": True,
    },
    {
        "room_number": "305",
        "room_type": "Family",
        "floor": 3,
        "price_per_night": 165,
        "max_guests": 4,
        "is_bookable": False,
    },
    {
        "room_number": "402",
        "room_type": "Suite",
        "floor": 4,
        "price_per_night": 220,
        "max_guests": 3,
        "is_bookable": True,
    },
]

# Main route for this API
@app.get("/")
def read_root():
    return RedirectResponse(url="/rooms-page", status_code=307)


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
    return [room for room in rooms_data if room["is_bookable"]]


@app.get("/rooms-page", response_class=HTMLResponse)
def rooms_page():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
        <title>Bookable Rooms</title>
        <style>
            * {
                box-sizing: border-box;
            }

            body {
                margin: 0;
                font-family: Arial, sans-serif;
                background: #f5f5f5;
                color: #222;
            }

            main {
                max-width: 800px;
                margin: 0 auto;
                padding: 24px 16px 40px;
            }

            .hero {
                margin-bottom: 16px;
            }

            h1 {
                margin: 0 0 8px;
                font-size: 32px;
            }

            .status {
                margin: 0;
                font-weight: bold;
            }

            .grid {
                display: flex;
                flex-direction: column;
                gap: 12px;
            }

            .card {
                background: #fff;
                border: 1px solid #ddd;
                border-radius: 8px;
                padding: 16px;
            }

            .room-type {
                margin: 0 0 8px;
                font-size: 20px;
            }

            .meta {
                margin: 0;
                padding: 0;
                list-style: none;
                line-height: 1.8;
            }
        </style>
    </head>
    <body>
        <main>
            <section class="hero">
                <h1>Available Rooms</h1>
                <p>Simple frontend using <code>fetch()</code> from <code>/rooms</code>.</p>
                <p class="status" id="status">Loading rooms...</p>
            </section>
            <section class="grid" id="room-list"></section>
        </main>

        <script>
            const statusElement = document.getElementById("status");
            const roomListElement = document.getElementById("room-list");

            async function loadRooms() {
                try {
                    const response = await fetch("/rooms");

                    if (!response.ok) {
                        throw new Error("Could not load rooms");
                    }

                    const rooms = await response.json();

                    statusElement.textContent = `${rooms.length} bookable room(s) found.`;

                    roomListElement.innerHTML = rooms.map((room) => `
                        <article class="card">
                            <h2 class="room-type">Room ${room.room_number} - ${room.room_type}</h2>
                            <ul class="meta">
                                <li><strong>Floor:</strong> ${room.floor}</li>
                                <li><strong>Guests:</strong> up to ${room.max_guests}</li>
                                <li><strong>Price:</strong> ${room.price_per_night} EUR / night</li>
                                <li><strong>Status:</strong> Bookable</li>
                            </ul>
                        </article>
                    `).join("");
                } catch (error) {
                    statusElement.textContent = "Could not load rooms right now.";
                    roomListElement.innerHTML = "";
                }
            }

            loadRooms();
        </script>
    </body>
    </html>
    """
