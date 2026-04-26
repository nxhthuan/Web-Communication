
const API_URL = "http://127.0.0.1:8080";
//const API_URL = "https://wdb26-english-examples-deployment-testing.2.rahtiapp.fi/api/ip";

async function getGuests() {
    const res = await fetch(`${API_URL}/guests`);
    const guests = await res.json();

    console.log(guests);

    const guestList = document.getElementById("guest-list");
    guestList.innerHTML = ""; // clear existing options

    for (const guest of guests) {
        guestList.innerHTML += `
            <option value="${guest.id}">
                ${guest.firstname} ${guest.lastname}
                (${guest.previous_visits} visits)
            </option>
        `;
    }
}

getGuests();

async function getRooms() {
    const res = await fetch(`${API_URL}/rooms`);
    const rooms = await res.json();

    console.log(rooms);
    document.getElementById("room-list").innerHTML = "";

    for (const room of rooms) {
        document.getElementById("room-list").innerHTML += `
            <option value="${room.id}">
                ${room.room_number} -
                ${room.type} -
                ${room.price} €
            </option>
        `;
    }
}
getRooms();


async function getBookings() {
    const res = await fetch(`${API_URL}/bookings`);
    const bookings = await res.json();

    console.log(bookings);
    document.getElementById("bookings-list").innerHTML = "";
    for (const b of bookings) {
        document.getElementById("bookings-list").innerHTML += `
            <li>
                ${b.id} - ${b.datefrom} 
                    - ${b.guest_name}
                    - ${b.number_of_nights} nights
                    - ${b.total_price} €
            </li>
        `;
    }
}
getBookings();

async function saveBooking() {

    const booking = {
        room_id: Number(document.getElementById("room-list").value),
        guest_id: Number(document.getElementById("guest-list").value),
        booking_date: document.getElementById("datefrom").value,
        dateto: document.getElementById("dateto").value,
        addinfo: document.getElementById("info").value
    }

    const res = await fetch(`${API_URL}/bookings`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(booking)
    });
    const resData = await res.json();

    console.log(resData);
    getBookings();
}


document.getElementById('btn-save').addEventListener('click', saveBooking);
