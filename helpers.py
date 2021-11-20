
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
   
def customportfolio_add(name, value):
    #CHECK IF ACC NAME IS IN DATABASE
    acc = query_db("SELECT * FROM customportfolio WHERE user_id = ? and accname = ?", (session["user_id"], name), one=True)

    #ADDS ACC TO DB IF NOT
    if not (acc):
        get_db().execute("INSERT INTO customportfolio (user_id, accname, value) VALUES (?, ?, ?)", (session["user_id"], name, value))
        get_db().commit()

def get_customportfolio(): 
    wl = query_db("SELECT accname, value FROM customportfolio WHERE user_id = ?", ([session["user_id"]]))
    return wl

def customportfolio_remove(accname):
    #checking ticker is in watchlist db
    if (query_db("SELECT * FROM customportfolio WHERE user_id = ? and accname = ?", (session["user_id"], accname), one=True)):
        get_db().execute("DELETE FROM customportfolio WHERE user_id = ? and accname = ?", (session["user_id"], accname))
        get_db().commit()

def setvalue_customportfolio(accname, value):
    #setting quantity of a single holding
    get_db().execute("UPDATE customportfolio SET value = ? WHERE user_id = ? and accname = ?", (value, session["user_id"], accname))
    get_db().commit()


def portfolio_add(ticker, quantity):
    #adds info to stock db
    add_to_stockdb(ticker)
    #CHECKS IF STOCK IS IN PORTFOLIO DATABASE
    stock = query_db("SELECT * FROM portfolio WHERE user_id = ? and stock_id = (SELECT id FROM stocks WHERE symbol = ?)", (session["user_id"], ticker), one=True)
    #ADDS TO PORTFOLIO DB IF NOT
    if not (stock):
        get_db().execute("INSERT INTO portfolio (user_id, stock_id, quantity) VALUES (?, (SELECT id FROM stocks WHERE symbol = ?), ?)", (session["user_id"], ticker, quantity))
        get_db().commit()

def portfolio_remove(ticker):
    #checking ticker is in watchlist db
    if (query_db("SELECT * FROM portfolio WHERE user_id = ? and stock_id = (SELECT id FROM stocks WHERE symbol = ?)", (session["user_id"], ticker), one=True)):
        get_db().execute("DELETE FROM portfolio WHERE user_id = ? and stock_id = (SELECT id FROM stocks WHERE symbol = ?)", (session["user_id"], ticker))
        get_db().commit()

def setquantity_portfolio(ticker, quantity):
    #setting quantity of a single holding
    get_db().execute("UPDATE portfolio SET quantity = ? WHERE user_id = ? and stock_id = (SELECT id FROM stocks WHERE symbol = ?)", (quantity, session["user_id"], ticker))
    get_db().commit()

def get_portfolio():
    #wl = query_db("SELECT * FROM stocks WHERE id IN (SELECT stock_id FROM portfolio WHERE user_id = ?)" [session["user_id"]])    
    wl = query_db("SELECT stocks.*, portfolio.quantity FROM stocks inner join portfolio on portfolio.stock_id = stocks.id WHERE id IN (SELECT stock_id FROM portfolio WHERE user_id = ?);", ([session["user_id"]]))
    return wl


def watchlist_add(ticker):
    #adds info to stock db
    add_to_stockdb(ticker)
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
    dictlist = []
    i = 0
    for company in li:
        price = get_price(company["symbol"])

        dictlist.append({"symbol":company["symbol"], 
                         "name":company["name"], 
                         "currency":company["currency"], 
                         "price":price["price"][-1],
                         "previousClose":price["prevClose"],
                         "daily_change": price["dailychange"],
                         "perc_daily_change": price["percdailychange"],
                         })

        if len(company) > 5:
            dictlist[i]["quantity"] = company["quantity"]
            dictlist[i]["value"] = dictlist[i]["quantity"] * dictlist[i]["price"]
        i+=1
    return dictlist

def get_price(ticker):
    stock = query_db("SELECT * FROM stocks WHERE symbol = ?", [ticker], one=True)
    tempprices = yf.Ticker(ticker).history(period='5y')
    tempprice = tempprices["Close"]

    if stock["quoteType"] == "INDEX":
        prevClose = yf.Ticker(ticker).info["previousClose"]
    elif stock["quoteType"] == "CURRENCY" and len(tempprice) == 1 :
        prevClose = tempprice[0]
    else:
        prevClose = tempprice[-2]
    prices = {}

    
    prices["price"] = tempprice
    prices["prevClose"] = prevClose
    prices["dailychange"] = tempprice[-1] - prevClose
    prices["percdailychange"] = prices["dailychange"] / tempprice[-1] * 100
    prices["prices"] = {"Date":tempprices.index.date, 
                        "Price":tempprice
                        }

    print(prices["prices"]["Date"][0], prices["prices"]["Price"][0])   

    return prices;

def add_to_stockdb(ticker):
    #CHECKS IF STOCK IS IN DATABASE
    user = query_db("SELECT * FROM stocks WHERE symbol = ?", [ticker], one=True)
    #ADDS TO DB IF NOT
    if not (user):
        company = yf.Ticker(ticker).info
        if (company["currency"] == None):
            get_db().execute("INSERT INTO stocks (symbol, name, currency, quoteType) VALUES (?, ?, ?, ?)", (company["symbol"], company["shortName"], "None", company["quoteType"]))
        else:
            get_db().execute("INSERT INTO stocks (symbol, name, currency, quoteType) VALUES (?, ?, ?, ?)", (company["symbol"], company["shortName"], company["currency"], company["quoteType"]))
        get_db().commit()


def get_conversion_rates(list):
    currencylist = []
    conversion_rates = {}
    #Makes list of currenct currencies in use
    for company in list:
        if company["currency"] not in currencylist:
            currencylist.append(company["currency"])
    #finds conversion rates
    for currency in currencylist:
        conversionticker = "GBP" + currency.upper() + "=X"
        conversion_rates.update ({currency : yf.Ticker(conversionticker).history(period='7d')["Close"][0]})
    
    return conversion_rates

#CURRENCY FORMATTERS

def currency(value, currency):
    """Format value as USD."""
    if currency.lower() == "usd":
        if value <= 0.1 and value > -0.1 and value != 0:
            return f"${value:,.3f}"
        else:
            return f"${value:,.2f}"
    elif currency == "GBp":
        if value <= 0.1 and value > -0.1 and value != 0:
            return f"{value:,.3f}p"
        elif value >= 100:
            return f"£{value/100:,.2f}"
        else:
            return f"{value:,.2f}p"
    elif currency == "GBP":
        return f"£{value:,.2f}"
    elif currency.lower() == "eur":
        return f"€{value:,.2f}"
    elif currency.lower() == "cad":
        return f"CAD${value:,.2f}"
    elif currency.lower() == "hkd":
        return f"HK${value:,.2f}"
    elif currency.lower() == "mxn":
        return f"{value:,.2f}MXN"
    elif currency.lower() == "ars":
        return f"{value:,.2f}ARS"
    elif currency.lower() == "sgd":
        return f"{value:,.2f}SGD"
    else:
        return f"{value:,.2f}?"


def converttogbp(value, conversion, currency):
    
    if currency == "GBp":
        gbpvalue = value / 100
    else:
        gbpvalue = value / conversion[currency]

    return f"£{gbpvalue:,.2f}"
    
def formatgbp(value):
    return f"£{value:,.2f}"


def percentage(value):
    return f"{value:,.2f}%"