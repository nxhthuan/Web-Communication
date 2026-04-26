
const API_URL = "http://127.0.0.1:8080";
//const API_URL = "https://wdb26-english-examples-deployment-testing.2.rahtiapp.fi/api/ip";

// TEMPORARY KEY, move to LocalStorage or similar
const API_KEY = "25e027713b889d7c81cedf7669bdec843bfc63e9e087d1fb68334e8cf4c88f68";

/*async function getGuests() {
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
getGuests();*/



async function getRooms() {
    const res = await fetch(`${API_URL}/rooms`);
    const rooms = await res.json();

    console.log(rooms);
    for (room of rooms) {
        document.getElementById("room-list").innerHTML += `
            <option value="${room.id}">
                ${room.room_number} -
                ${room.room_type} -
                ${room.price} €
            </option>
        `;
    }
}
getRooms();

async function updateBooking(booking_id, data) {
    const res = await fetch(`${API_URL}/bookings/${booking_id}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
            'X-API-Key': API_KEY
        },
        body: JSON.stringify(data)
    });
    const resData = await res.json();
    console.log(resData);

    getBookings();
}


function saveStars(booking_id, stars) {
    console.log(`booking ${booking_id} gets ${stars} stars`);
    // add PUT/PATCH request here...
    updateBooking(booking_id, { stars: stars });
}

async function getBookings() {
    const res = await fetch(`${API_URL}/bookings`, {
        headers: { 'X-API-Key': API_KEY }
    });
    const bookings = await res.json();

    console.log(bookings);
    document.getElementById("bookings-list").innerHTML = "";
    for (b of bookings) {
        document.getElementById("bookings-list").innerHTML += `
            <li>
                ${b.id} - ${b.datefrom} 
                    - ${b.guest_name}
                    - ${b.nights} nights
                    - ${b.total_price} €
                    <select id="stars-${b.id}" onchange="saveStars(${b.id}, this.value)">
                        <option value="1">⭐</option>
                        <option value="2">⭐⭐</option>
                        <option value="3">⭐⭐⭐</option>
                        <option value="4">⭐⭐⭐⭐</option>
                        <option value="5">⭐⭐⭐⭐⭐</option>
                    </select> (stars: ${b.stars || ""})
            </li>
        `;
    }
}
getBookings();

async function getMonthlyReport() {
    const res = await fetch(`${API_URL}/monthly-report`, {
        headers: { 'X-API-Key': API_KEY }
    });
    const reportRows = await res.json();

    console.log(reportRows);
    document.getElementById("monthly-report-list").innerHTML = "";

    for (r of reportRows) {
        document.getElementById("monthly-report-list").innerHTML += `
            <tr>
                <td>${r.month}</td>
                <td>${r.number_of_bookings}</td>
                <td>${r.number_of_nights}</td>
                <td>${r.revenue} â‚¬</td>
            </tr>
        `;
    }
}
getMonthlyReport();

async function saveBooking() {

    const booking = {
        room_id: document.getElementById("room-list").value,
        //guest_id: document.getElementById("guest-list").value,
        datefrom: document.getElementById("datefrom").value,
        dateto: document.getElementById("dateto").value,
        info: document.getElementById("info").value
    }

    const res = await fetch(`${API_URL}/bookings`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-API-Key': API_KEY
        },
        body: JSON.stringify(booking)
    });
    const resData = await res.json();

    console.log(resData);
    getBookings();
    getMonthlyReport();
}

document.getElementById('btn-save').addEventListener('click', saveBooking);
