
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware

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
