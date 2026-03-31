
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
    </head>
    <body>
        <main>
            <h1>Available rooms list</h1>
            <p id="status">Loading rooms...</p>
            <hr />
            <div id="room-list"></div>
        </main>

        <script>
            const statusElement = document.getElementById("status");
            const roomListElement = document.getElementById("room-list");

            async function loadRooms() {
                statusElement.textContent = "Loading rooms...";
                roomListElement.innerHTML = "";

                const response = await fetch("/rooms");
                const rooms = await response.json();

                statusElement.textContent = `${rooms.length} bookable room(s) found.`;

                if (rooms.length === 0) {
                    roomListElement.innerHTML = "<p>No rooms available right now.</p>";
                    return;
                }

                roomListElement.innerHTML = rooms.map((room) => `
                    <section>
                        <h2>Room ${room.room_number}</h2>
                        <p>Type: ${room.room_type}</p>
                        <p>Floor: ${room.floor}</p>
                        <p>Pax: up to ${room.max_guests}</p>
                        <p>Price: ${room.price_per_night} EUR</p>
                        <hr />
                    </section>
                `).join("");
            }

            loadRooms();
        </script>
    </body>
    </html>
    """
