from datetime import date

from fastapi import FastAPI, Response, HTTPException

from hashlib import sha256
from random import random

from starlette.responses import HTMLResponse

app = FastAPI()

app.secret_key = "NotSoSecurePa$$"
app.login = "4dm1n"
app.access_tokens = []



@app.get("/hello")
async def read_items():
    curr_date = date.today()
    curr = curr_date.strftime('%Y-%m-%d')
    html_content = """
    <html>
        <head>
            <title>Some HTML in here</title>
        </head>
        <body>
            <h1>Hello! Today date is YYYY-MM-DD</h1>
        </body>
    </html>
    """
    return HTMLResponse(content=html_content.replace('YYYY-MM-DD', curr), status_code=200)


@app.post("/login_session", status_code=201)
def login(user: str, password: str, response: Response):
    session_token = sha256(f"{user}{password}{app.secret_key}".encode()).hexdigest()
    app.access_tokens.append(session_token)
    if user != app.login:
        raise HTTPException(status_code=401)
    if password != app.secret_key:
        raise HTTPException(status_code=401)
    response.set_cookie(key="session_token", value=session_token)
    return response


@app.post("/login_token", status_code=201)
def token(user: str, password: str):
    if user != app.login:
        raise HTTPException(status_code=401)
    if password != app.secret_key:
        raise HTTPException(status_code=401)
    return {"token": random.choice()}


@app.get("/test")
def test():
    return "test"
