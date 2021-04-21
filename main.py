import datetime
from fastapi import FastAPI, Response
import hashlib

from pydantic import BaseModel

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
    global counter

    curr_date = datetime.datetime.today()
    vacc_date = curr_date + datetime.timedelta(days=1)

    curr = curr_date.strftime('%Y-%m-%d')
    vacc = vacc_date.strftime('%Y-%m-%d')
    ret = {
        "id": counter,
        "name": person.name,
        "surname": person.surname,
        "register_date": curr,
        "vaccination_date": vacc

    }
    counter += 1

    return ret
