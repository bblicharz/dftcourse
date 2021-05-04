from cgitb import html
from datetime import date
from typing import Optional

from fastapi import FastAPI, Response, HTTPException, Cookie

from hashlib import sha256
from random import random, choice

from pydantic import json
from starlette import status
from starlette.responses import HTMLResponse, PlainTextResponse, RedirectResponse, JSONResponse

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


# @app.post("/login_session", status_code=201)
# def login(user: str, password: str, response: Response):
#     session_token = sha256(f"{user}{password}{app.secret_key}".encode()).hexdigest()
#     app.access_tokens.append(session_token)
#     if user != app.login:
#         raise HTTPException(status_code=401)
#     if password != app.secret_key:
#         raise HTTPException(status_code=401)
#     response.set_cookie(key="session_token", value=session_token)
#     return response
#
#
# @app.post("/login_token", status_code=201)
# def token(user: str, password: str):
#     if user != app.login:
#         raise HTTPException(status_code=401)
#     if password != app.secret_key:
#         raise HTTPException(status_code=401)
#     return {"token": random.choice()}

from fastapi import Depends, FastAPI
from fastapi.security import HTTPBasic, HTTPBasicCredentials

security = HTTPBasic()

cookie_session = None
new_token = None




@app.post("/login_session")
def login_session(response: Response, credentials: HTTPBasicCredentials = Depends(security)):
    authenticate(credentials)
    global cookie_session
    cookie_session = "a"
    response.set_cookie(key="session_token", value=cookie_session)
    response.status_code = status.HTTP_201_CREATED
    return response


def authenticate(credentials):
    if credentials.username != '4dm1n' and credentials.password != 'NotSoSecurePa$$':
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)


@app.post("/login_token")
def login_token(response: Response, credentials: HTTPBasicCredentials = Depends(security)):
    authenticate(credentials)
    global new_token
    new_token = 'b'
    response.status_code = status.HTTP_201_CREATED
    return {"token": new_token}


def format_response(format):
    if format == 'json':
        return {"message": "Welcome!"}
    elif format == 'html':
        content = '<h1>Welcome!</h1>'
        return HTMLResponse(content=content)
    else:
        content = 'Welcome!'
        return PlainTextResponse(content=content)

def format_farewell(format):
    if format == 'json':
        content = {"message": "Logged out!"}
        return JSONResponse(content=content)
    elif format == 'html':
        content = '<h1>Logged out!</h1>'
        return HTMLResponse(content=content)
    else:
        content = 'Logged out!'
        return PlainTextResponse(content=content)


@app.get("/welcome_session")
def welcome_session(response: Response, session_token: Optional[str] = Cookie(None), format=None):
    if session_token != cookie_session:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    response.status_code = status.HTTP_200_OK
    return format_response(format)


@app.get("/welcome_token")
def welcome_token(response: Response, token: Optional[str], format=None):
    if token != new_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    response.status_code = status.HTTP_200_OK
    return format_response(format)


@app.delete('/logout_session')
def logout_session(response: Response, session_token: Optional[str] = Cookie(None), format=None):
    global cookie_session
    if session_token != cookie_session:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    cookie_session = None
    return redirect_response(response, format)


@app.delete('/logout_token')
def logout_token(response: Response, token: Optional[str], format=None):
    global new_token
    if token != new_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    new_token = None
    return redirect_response(response, format)


def redirect_response(response, format=None):
    response.status_code = status.HTTP_302_FOUND
    path = '/logged_out'
    if format:
        path = path + f'?format={format}'

    return RedirectResponse(path, status_code=302)


@app.get('/logged_out')
def logged_out(response: Response, format=None):
    response.status_code = status.HTTP_200_OK
    return format_farewell(format)

