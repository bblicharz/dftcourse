from fastapi import FastAPI, Response
import hashlib

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

    hashed = hashlib.sha512(password.encode()).hexdigest()
    if hashed == password_hash:
        response.status_code = 204
    else:
        response.status_code = 401
    return response
