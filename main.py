from datetime import date, datetime

from fastapi import FastAPI, Response
import hashlib

from pydantic import BaseModel
from starlette.requests import Request

app = FastAPI()


@app.get("/")
def root():
    return {"message": "Hello world!"}


@app.get("/method")
def method():
    return {"method": "GET"}


@app.delete("/method")
def method():
    return {"method": "DELETE"}


@app.put("/method")
def method():
    return {"method": "PUT"}


@app.options("/method")
def method():
    return {"method": "OPTIONS"}


@app.post("/method", status_code=201)
def method():
    return {"method": "POST"}


@app.get("/auth")
def auth(response: Response, password=None, password_hash=None):
    if password is None or password_hash is None:
        response.status_code = 401
        return response
    # TODO
    hashed = hashlib.sha512(password.encode()).hexdigest()
    if hashed == password_hash:
        response.status_code = 204
    else:
        response.status_code = 401
    return response


_DB = {}
counter = 1

class Person(BaseModel):
    name: str
    surname: str



@app.post("/register", status_code=201)
def register(person: Person):
    global _DB
    global counter

    daysnum = len(person.name) + len(person.surname)

    curr_date = datetime.datetime.today()
    vacc_date = curr_date + datetime.timedelta(days=daysnum)

    curr = curr_date.strftime('%Y-%m-%d')
    vacc = vacc_date.strftime('%Y-%m-%d')
    ret = {
        "id": counter,
        "name": person.name,
        "surname": person.surname,
        "register_date": curr,
        "vaccination_date": vacc

    }

    _DB[counter] = ret
    counter = counter + 1

    return ret


@app.get("/patient/{item_id}")
def patient(response: Response, item_id: int):
    if item_id < 1:
        response.status_code = 400
        return response

    global _DB

    pat = _DB.get(item_id)
    if pat is None:
        response.status_code = 404
        return response
    else:
        return pat

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI()


@app.get("/date/")
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


