
from werkzeug.security import generate_password_hash, check_password_hash
from flask import redirect, session, Flask, g
from functools import wraps
import sqlite3, yfinance as yf

def password_check(password, password_conf):
    if password != password_conf:
        return None;
    else:
        return generate_password_hash(password, method='pbkdf2:sha256', salt_length=8)

def login_required(f):
    #decorator wrap taken from https://flask.palletsprojects.com/en/1.1.x/patterns/viewdecorators/
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated_function

def get_db():
    db = getattr(g, '_database', None)
    
    if db is None:
        db = g._database = sqlite3.connect("financeer.db")
    db.row_factory = sqlite3.Row
    return db

def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv

def check_login_details(login, pw):
    if (login == '' or pw == ''):
        return("Empty Fields")
    elif (not query_db("SELECT * FROM users WHERE username = ? or email = ?", (login, login), one=True)):
        return("Username / Email does not exist")
    elif (not check_password_hash(query_db("SELECT hash FROM users WHERE username = ? or email = ?", (login, login), one=True)["hash"], pw)):
        return("Password Incorrect")
    else:
        return None

def check_signup_details(username, email, pw, pw_conf):
    if (username == '' or email == '' or pw == '' or pw_conf == ''):
        return("Empty Fields")
    elif (query_db("SELECT id FROM users WHERE username = ?", [username], one=True) ):
        return("Username already exists")
    elif (query_db("SELECT id FROM users WHERE email = ?", [email], one=True) ):
        return("Email already exists")
    elif (pw != pw_conf):
        return("Passwords do not match")
    else:
        return None

def store_session(login, permanent):
    user = query_db("SELECT * FROM users WHERE username = ? or email = ?", (login, login), one=True)
    if (permanent):
        session.permanent = True
    session["user_id"] = user["id"]
    session["user_name"] = user["username"]
    
def watchlist_add(ticker):
    #CHECKS IF STOCK IS IN DATABASE
    user = query_db("SELECT * FROM stocks WHERE symbol = ?", [ticker], one=True)
    #ADDS TO DB IF NOT
    if not (user):
        company = yf.Ticker(ticker).info
        get_db().execute("INSERT INTO stocks (symbol, name, currency) VALUES (?, ?, ?)", (company["symbol"], company["shortName"], company["currency"]))
        get_db().commit()
    #CHECKS IF STOCK IS IN WATCHLIST DATABASE
    stock = query_db("SELECT * FROM user_stocks WHERE user_id = ? and stock_id = (SELECT id FROM stocks WHERE symbol = ?)", (session["user_id"], ticker), one=True)
    #ADDS TO WATCHLIST DB IF NOT
    if not (stock):
        get_db().execute("INSERT INTO user_stocks (user_id, stock_id) VALUES (?, (SELECT id FROM stocks WHERE symbol = ?))", (session["user_id"], ticker))
        get_db().commit()

def watchlist_remove(ticker):
    #checking ticker is in watchlist db
    if (query_db("SELECT * FROM user_stocks WHERE user_id = ? and stock_id = (SELECT id FROM stocks WHERE symbol = ?)", (session["user_id"], ticker), one=True)):
        get_db().execute("DELETE FROM user_stocks WHERE user_id = ? and stock_id = (SELECT id FROM stocks WHERE symbol = ?)", (session["user_id"], ticker))
        get_db().commit()

def get_watchlist():
    wl = query_db("SELECT * FROM stocks WHERE id IN (SELECT stock_id FROM user_stocks WHERE user_id = ?)", [session["user_id"]])    
    return wl

def get_prices(li):
    dict = {}
    dictlist = []
    i = 0
    for company in li:
        dictlist.append({"symbol":company["symbol"], 
                         "name":company["name"], 
                         "currency":company["currency"], 
                         "price":yf.Ticker(company["symbol"]).history(period='7d')["Close"][-1]
                         })
    print(dictlist)
    return dictlist

#CURRENCY FORMATTERS

def currency(value, currency):
    """Format value as USD."""
    if currency.lower() == "usd":
        return f"${value:,.2f}"
    elif currency.lower() == "gbp":
        return f"{value:,.2f}p"
    