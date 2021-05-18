import string
from datetime import date
from random import choice
from typing import Optional, OrderedDict, Dict, List

from fastapi import FastAPI, Response, HTTPException, Cookie
from sqlalchemy import desc
from sqlalchemy.orm import Session

from starlette import status
from starlette.responses import HTMLResponse, PlainTextResponse, RedirectResponse, JSONResponse

import sqlite3

from database import get_db
from models import Supplier, Product, Category

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
async def categories(response: Response):
    app.db_connection.row_factory = sqlite3.Row
    data = app.db_connection.execute('SELECT CategoryID, CategoryName FROM Categories ORDER BY CategoryID').fetchall()
    response.status_code = status.HTTP_200_OK
    return {"categories": [{"id": x['CategoryID'], "name": x["CategoryName"]} for x in data]}


@app.get("/customers")
async def customers(response: Response):
    app.db_connection.row_factory = sqlite3.Row
    data = app.db_connection.execute('SELECT * FROM Customers ORDER BY UPPER(CustomerID)').fetchall()
    response.status_code = status.HTTP_200_OK
    ret = []
    for x in data:
        address = x['Address'] or ''
        postal_code = x['PostalCode'] or ''
        city = x['City'] or ''
        country = x['Country'] or ''
        full_address = ' '.join([address, postal_code, city, country])
        ret.append({
            'id': x['CustomerID'],
            'name': x['CompanyName'],
            'full_address': full_address
        })

    return {"customers": ret}


@app.get("/products/{id}")
async def products_id(response: Response, id: int):
    app.db_connection.row_factory = sqlite3.Row
    data = app.db_connection.execute("SELECT ProductID, ProductName FROM Products WHERE ProductID = ?", (id,)).fetchone()
    if data is None:
        response.status_code = status.HTTP_404_NOT_FOUND
        return
    response.status_code = status.HTTP_200_OK
    return {'id': data['ProductID'], 'name': data['ProductName']}


@app.get("/employees")
async def employees(
        response: Response,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        order: Optional[str] = None,
):
    valid_ordering_columns = {
        'first_name': 'FirstName',
        'last_name': 'LastName',
        'city': 'City',
        None: 'EmployeeId'
    }
    ordering_column = valid_ordering_columns.get(order)

    if ordering_column is None:
        raise HTTPException(status_code=400)

    app.db_connection.row_factory = sqlite3.Row

    query = "SELECT EmployeeID, LastName, FirstName, City FROM Employees ORDER BY {}".format(ordering_column)

    if limit is not None and offset is not None:
        data = app.db_connection.execute(
            query + " LIMIT ? OFFSET ?", (limit, offset)).fetchall()

    elif limit is not None:
        data = app.db_connection.execute(query + " LIMIT ?", (limit,)).fetchall()
    elif offset is not None:
        data = app.db_connection.execute(query + " LIMIT -1 OFFSET ?", (offset,)).fetchall()
    else:
        data = app.db_connection.execute(query).fetchall()
    response.status_code = status.HTTP_200_OK
    return {"employees": [{"id": x['EmployeeID'], "last_name": x["LastName"], "first_name": x["FirstName"], "city": x["City"]} for x in data]}


@app.get('/products_extended')
async def products_extended(response: Response):
    app.db_connection.row_factory = sqlite3.Row
    data = app.db_connection.execute(
        '''
            SELECT Products.ProductID, Products.ProductName, Categories.CategoryName, Suppliers.CompanyName
            FROM Products JOIN Categories ON Products.CategoryID = Categories.CategoryID 
            JOIN Suppliers ON Products.SupplierID = Suppliers.SupplierID ORDER BY ProductID;
        ''').fetchall()
    response.status_code = status.HTTP_200_OK
    return {
        "products_extended": [
               {
                   "id": x['ProductID'],
                   "name": x['ProductName'],
                   "category": x["CategoryName"],
                   "supplier": x["CompanyName"],
               } for x in data
          ]
    }

@app.get('/products/{id}/orders')
async def products_id_orders(response: Response, id: int):
    app.db_connection.row_factory = sqlite3.Row
    data = app.db_connection.execute(
        '''
        SELECT Orders.OrderID, Customers.CompanyName, "Order Details".*
        FROM Orders 
        JOIN Customers ON Orders.CustomerID = Customers.CustomerID 
        JOIN "Order Details" ON Orders.OrderID = "Order Details".OrderID 
        WHERE ProductID = ?
        Order by Orders.OrderID
        ''',
        (id,)
    ).fetchall()

    if not data:
        raise HTTPException(status_code=404)
    else:
        response.status_code = status.HTTP_200_OK
        return {
            "orders": [
                   {
                       "id": x['OrderID'],
                       "customer": x['CompanyName'],
                       "quantity": x["Quantity"],
                       "total_price": round((x['UnitPrice'] * x['Quantity']) - (x['Discount'] * (x['UnitPrice'] * x['Quantity'])),2)
                   } for x in data
              ]
        }



@app.post('/categories')
async def categories(response: Response, category: Dict):
    app.db_connection.row_factory = sqlite3.Row
    app.db_connection.execute(
        'INSERT INTO Categories (CategoryName) VALUES (?)',
        (category['name'],)
    )

    raw_data = app.db_connection.execute('SELECT last_insert_rowid()').fetchall()
    last_id = raw_data[0]["last_insert_rowid()"]
    response.status_code = status.HTTP_201_CREATED
    category['id'] = last_id
    return category


@app.put('/categories/{id}')
async def categories(response: Response, id: int, category: Dict):
    app.db_connection.row_factory = sqlite3.Row
    data = app.db_connection.execute(
        'SELECT CategoryID FROM Categories WHERE CategoryID = ?',
        (id,)
    ).fetchall()

    if not data:
        raise HTTPException(404)

    app.db_connection.execute(
        '''
        UPDATE Categories SET CategoryName = ?
        WHERE CategoryID = ?
        ''',
        (category['name'], id)
    )

    category["id"] = id
    return category


@app.delete('/categories/{id}')
async def categories(response: Response, id: int):
    app.db_connection.row_factory = sqlite3.Row
    data = app.db_connection.execute(
        'SELECT CategoryID FROM Categories WHERE CategoryID = ?',
        (id,)
    ).fetchall()

    if not data:
        raise HTTPException(404)

    app.db_connection.execute(
        '''
        DELETE FROM Categories
        WHERE CategoryID = ?
        ''',
        (id,)
    )
    return {"deleted": 1}


@app.get('/suppliers')
def suppliers(db: Session = Depends(get_db)):
    db_suppliers: List[Supplier] = db.query(Supplier).order_by(Supplier.SupplierID).all()
    return [{"SupplierID": x.SupplierID, "CompanyName": x.CompanyName} for x in db_suppliers]


@app.get('/suppliers/{id}')
def suppliers_id(id: int, db: Session = Depends(get_db)):
    db_supplier: Supplier = db.query(Supplier).filter(Supplier.SupplierID == id).one_or_none()
    if db_supplier is None:
        raise HTTPException(status_code=404)
    return {
            "SupplierID": db_supplier.SupplierID,
            "CompanyName": db_supplier.CompanyName,
            "ContactName": db_supplier.ContactName,
            "ContactTitle": db_supplier.ContactTitle,
            "Address": db_supplier.Address,
            "City": db_supplier.City,
            "Region": db_supplier.Region,
            "PostalCode": db_supplier.PostalCode,
            "Country": db_supplier.Country,
            "Phone": db_supplier.Phone,
            "Fax": db_supplier.Fax,
            "HomePage": db_supplier.HomePage
        }


@app.get('/suppliers/{id}/products')
def suppliers_id_products(id: int, db: Session = Depends(get_db)):
    db_products: List[Product] = (
        db.query(Product, Category)
            .join(Category, Product.CategoryID==Category.CategoryID)
            .filter(Product.SupplierID == id)
            .order_by(desc(Product.ProductID)).
            all()
    )
    if not db_products:
        raise HTTPException(status_code=404)
    return [
        {'ProductID': p.ProductID,
         'ProductName': p.ProductName,
         "Category": {"CategoryID": c.CategoryID, "CategoryName": c.CategoryName},
         'Discontinued': p.Discontinued
         } for p, c in db_products]

@app.post('/suppliers')
def suppliers(suppliers: Dict, response: Response, db: Session = Depends(get_db)):
    db_suppliers = db.query(Supplier).all()
    for var, value in vars(suppliers).items():
        setattr(db_suppliers, var, value) if value else None
    db.add(db_suppliers)
    db.commit()
    db.refresh(db_suppliers)
    return db_suppliers



