
from typing import List

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
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
    # f-string concatenation
    return { "msg": f"Hello {my_name}"}

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
            :root {
                --bg: #f6efe5;
                --card: #fffaf4;
                --ink: #1f2937;
                --accent: #b45309;
                --accent-soft: #fde6c8;
                --border: #ead8bf;
            }

            * {
                box-sizing: border-box;
            }

            body {
                margin: 0;
                min-height: 100vh;
                font-family: Georgia, "Times New Roman", serif;
                background:
                    radial-gradient(circle at top right, #ffe7bf 0, transparent 25%),
                    linear-gradient(180deg, #fff8ef 0%, var(--bg) 100%);
                color: var(--ink);
            }

            main {
                max-width: 1000px;
                margin: 0 auto;
                padding: 48px 20px 64px;
            }

            .hero {
                padding: 28px;
                border: 1px solid var(--border);
                border-radius: 24px;
                background: rgba(255, 250, 244, 0.92);
                box-shadow: 0 18px 50px rgba(91, 62, 31, 0.08);
            }

            h1 {
                margin: 0 0 12px;
                font-size: clamp(2.2rem, 5vw, 4rem);
                line-height: 1;
            }

            p {
                margin: 0;
                font-size: 1.05rem;
                line-height: 1.7;
            }

            .status {
                margin: 18px 0 0;
                color: var(--accent);
                font-weight: 700;
            }

            .grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
                gap: 18px;
                margin-top: 28px;
            }

            .card {
                padding: 20px;
                border-radius: 20px;
                border: 1px solid var(--border);
                background: var(--card);
                box-shadow: 0 14px 35px rgba(91, 62, 31, 0.08);
            }

            .room-number {
                display: inline-block;
                margin-bottom: 12px;
                padding: 6px 10px;
                border-radius: 999px;
                background: var(--accent-soft);
                color: var(--accent);
                font-weight: 700;
            }

            .room-type {
                margin: 0 0 12px;
                font-size: 1.4rem;
            }

            .meta {
                margin: 0;
                padding: 0;
                list-style: none;
                display: grid;
                gap: 8px;
            }

            .meta strong {
                color: #111827;
            }

            @media (max-width: 640px) {
                main {
                    padding-top: 28px;
                }

                .hero,
                .card {
                    border-radius: 18px;
                }
            }
        </style>
    </head>
    <body>
        <main>
            <section class="hero">
                <h1>Available Rooms</h1>
                <p>This page uses JavaScript <code>fetch()</code> to load the temporary room list from the FastAPI endpoint <code>/rooms</code>.</p>
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
                            <span class="room-number">Room ${room.room_number}</span>
                            <h2 class="room-type">${room.room_type}</h2>
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
