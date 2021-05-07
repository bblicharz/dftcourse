import string
from datetime import date
from random import choice
from typing import Optional, OrderedDict

from fastapi import FastAPI, Response, HTTPException, Cookie


from starlette import status
from starlette.responses import HTMLResponse, PlainTextResponse, RedirectResponse, JSONResponse

import sqlite3

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


class LRU(OrderedDict):
    'Limit size, evicting the least recently looked-up key when full'

    def __init__(self, maxsize=128, *args, **kwds):
        self.maxsize = maxsize
        super().__init__(*args, **kwds)

    # def __getitem__(self, key):
    #     value = super().__getitem__(key)
    #     self.move_to_end(key)
    #     return value

    def __setitem__(self, key, value):
        if key in self:
            self.move_to_end(key)
        super().__setitem__(key, value)
        if len(self) > self.maxsize:
            oldest = next(iter(self))
            del self[oldest]


cookie_db = LRU(maxsize=3)
token_db = LRU(maxsize=3)


def random_string(length):
    return ''.join(choice(string.ascii_letters) for i in range(length))


@app.post("/login_session")
def login_session(response: Response, credentials: HTTPBasicCredentials = Depends(security)):
    authenticate(credentials)
    cookie_session = random_string(10)
    cookie_db[cookie_session] = None
    response.set_cookie(key="session_token", value=cookie_session)
    response.status_code = status.HTTP_201_CREATED
    return response


def authenticate(credentials):
    if credentials.username != '4dm1n' and credentials.password != 'NotSoSecurePa$$':
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)


@app.post("/login_token")
def login_token(response: Response, credentials: HTTPBasicCredentials = Depends(security)):
    authenticate(credentials)
    new_token = random_string(10)
    token_db[new_token] = None
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
    if session_token not in cookie_db:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    response.status_code = status.HTTP_200_OK
    return format_response(format)


@app.get("/welcome_token")
def welcome_token(response: Response, token: Optional[str], format=None):
    if token not in token_db:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    response.status_code = status.HTTP_200_OK
    return format_response(format)


@app.delete('/logout_session')
def logout_session(response: Response, session_token: Optional[str] = Cookie(None), format=None):
    if session_token not in cookie_db:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    cookie_db.pop(session_token)
    return redirect_response(response, format)


@app.delete('/logout_token')
def logout_token(response: Response, token: Optional[str], format=None):
    if token not in token_db:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    token_db.pop(token)
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

@app.on_event("startup")
async def startup():
    app.db_connection = sqlite3.connect("northwind.db")
    app.db_connection.text_factory = lambda b: b.decode(errors="ignore")  # northwind specific


@app.on_event("shutdown")
async def shutdown():
    app.db_connection.close()


@app.get("/categories")
async def categories():
    app.db_connection.row_factory = sqlite3.Row
    data = app.db_connection.execute('SELECT CategoryID, CategoryName FROM Categories ORDER BY CategoryID').fetchall()
    return {"categories": [{"id": x['CategoryID'], "name": x["CategoryName"]} for x in data]}