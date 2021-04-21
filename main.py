from fastapi import FastAPI

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
