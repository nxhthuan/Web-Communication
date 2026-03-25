from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse

app = FastAPI()


def render_ip_html(client_ip: str, include_greeting: bool = False) -> str:
    if include_greeting:
        return f"<h1>Bonjour Anthony</h1><h2>Your public IP is {client_ip}</h2>"
    return f"<h1>Your public IP is {client_ip}</h1>"


@app.get("/", response_class=HTMLResponse)
def read_root(request: Request):
    client_ip = request.client.host
    return render_ip_html(client_ip, include_greeting=True)


@app.get("/api/ip")
def get_ip(request: Request):
    client_ip = request.client.host
    return {"ip": client_ip}


@app.get("/ip", response_class=HTMLResponse)
def get_ip_html(request: Request):
    client_ip = request.client.host
    return render_ip_html(client_ip)
