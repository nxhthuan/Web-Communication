from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse

app = FastAPI()


@app.get("/")
def read_root():
    return {"message": "Bonjour Anthony"}


@app.get("/api/ip")
def get_ip(request: Request):
    client_ip = request.client.host
    return {"ip": client_ip}


@app.get("/ip", response_class=HTMLResponse)
def get_ip_html(request: Request):
    client_ip = request.client.host
    return f"<h1>Your public IP is {client_ip}</h1>"