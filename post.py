from hashlib import sha256
from random import random

from fastapi import HTTPException, Response

from main import app

app.secret_key = "NotSoSecurePa$$"
app.login = "4dm1n"
app.access_tokens = []

@app.post("/login_session/", status_code=201)
def login(user: str, password: str, response: Response):
    session_token = sha256(f"{user}{password}{app.secret_key}".encode()).hexdigest()
    app.access_tokens.append(session_token)
    if user != app.login:
        raise HTTPException(status_code=401)
    if password != app.secret_key:
        raise HTTPException(status_code=401)
    response.set_cookie(key="session_token", value=session_token)
    return response

@app.post("/login_token/", status_code=201)
def token(user: str, password: str):
    if user != app.login:
        raise HTTPException(status_code=401)
    if password != app.secret_key:
        raise HTTPException(status_code=401)
    return {"token": random.choice()}

@app.get("/test")
def test():
    return "test"