"""
This script runs the application using a development server.
It contains the definition of routes and views for the application.
"""

from flask import Flask, render_template, session, request, flash, redirect, g
from werkzeug.security import generate_password_hash, check_password_hash
from helpers import password_check, login_required, get_db, query_db, check_signup_details, check_login_details, store_session, watchlist_add, get_watchlist, get_prices, watchlist_remove, add_to_stockdb, get_price, portfolio_add, get_portfolio, portfolio_remove, get_portfolio, setquantity_portfolio
from helpers import currency, percentage, converttogbp, get_conversion_rates, formatgbp, customportfolio_add, get_customportfolio, customportfolio_remove, setvalue_customportfolio
from datetime import timedelta
import sqlite3, yfinance as yf, requests, json
#from yfinance_help import ticker_info_dict

#gitcheck

app = Flask(__name__)

app.config.update(
    TESTING=True,
    TEMPLATES_AUTO_RELOAD=True,
    SECRET_KEY="Your_secret_string",
    SESSION_REFRESH_EACH_REQUEST =True,
    PERMANENT_SESSION_LIFETIME= timedelta(days=7)
)

# Custom filtera
app.jinja_env.filters["currency"] = currency
app.jinja_env.filters["percentage"] = percentage
app.jinja_env.filters["converttogbp"] = converttogbp
app.jinja_env.filters["formatgbp"] = formatgbp

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


@app.route('/')
@login_required
def home():
    """Renders a sample page."""
    return render_template("index.html")


@app.route('/search', methods=["GET", "POST"])
def search():
    if request.method == "GET":
        if session["search_change"] == True:
            session["search_change"] = False
            getsearchlist(session["search_term"])
            return render_template("search.html", data = session["last_search"])  
        return render_template("search.html")

    if request.method == "POST":
        if ("search" in request.form):
            session["search_term"] = request.form["search"]
            getsearchlist(session["search_term"])
            return render_template("search.html", data = session["last_search"])  
        elif ("watch" in request.form):
            watchlist_add(request.form['watch'])
        elif ("removewatch" in request.form):
            watchlist_remove(request.form['removewatch'])
        elif ("portfolio" in request.values):
            portfolio_add(request.form["companySymbol"], request.form["quantity"])
        elif ("removeportfolio" in request.form):
            portfolio_remove(request.form['removeportfolio'])
        session["search_change"] = True
        return redirect('search')        


@app.route('/stock', defaults={'ticker' : None}, methods=["GET", "POST"])
@app.route('/stock/<ticker>', methods=["GET", "POST"])
def stock(ticker):

    if request.method == "POST":
        if "watch" in request.form:
            watchlist_add(ticker)
        elif "removewatch" in request.form:
            watchlist_remove(ticker)
    if ticker:
        add_to_stockdb(ticker)
        company = yf.Ticker(ticker).info
        price = {}
        price = get_price(ticker)
        watch = get_watchlist()
        watched = False
        for comp in watch:
            if ticker == comp["symbol"]:
                watched = True

    return render_template("stock.html", company=company, price=price, watched=watched)

@app.route('/watchlist', methods=["GET", "POST"])
def watchlist():

    if request.method == "POST":
        if ("removewatch" in request.form):
            watchlist_remove(request.form['removewatch'])
            for i in range(len(session["watchlist"])):
                if (session["watchlist"][i]["symbol"] == request.form['removewatch']):
                    del session["watchlist"][i]
                    session["watchlist"] = session["watchlist"]
                    break
            return render_template('watchlist.html', companies=session["watchlist"])   
    elif request.method == "GET":
        list = get_watchlist()
        dict = get_prices(list)
        session["watchlist"] = dict
        return render_template('watchlist.html', companies=session["watchlist"])

@app.route('/portfolio', methods=["GET", "POST"])
def portfolio():
    if request.method == "POST":
        if ("setPortfolioQuantity" in request.values):
            setquantity_portfolio(request.form["CompanySymbol"], request.form["AccountQuantity"])
        elif ("removePortfolio" in request.values):
            portfolio_remove(request.form["CompanySymbol"])
        elif ("newaccount" in request.values):
            accname = request.form["AccountName"]
            accvalue = request.form["AccountValue"]
            customportfolio_add(accname, accvalue)
        elif ("deleteaccount" in request.values):
            customportfolio_remove(request.form["AccountName"])
        elif ("changeaccountvalue" in request.values):
            setvalue_customportfolio(request.form["AccountName"], request.form["AccountValue"])



    list = get_portfolio()
    dict = get_prices(list)
    session["portfolio"] = dict
    conversion_rates = get_conversion_rates(session["portfolio"])
    stock_total = 0
    custom_total = 0
    total_value = 0
    for company in session["portfolio"]:
        if company["currency"] == "GBp":
            stock_total += (company["price"] * company["quantity"] / 100)
        else:
            stock_total += company["price"] / conversion_rates[company["currency"]] * company["quantity"]
    custom_accounts = get_customportfolio()
    for acc in custom_accounts:
        custom_total += acc["value"]
    total_value = stock_total + custom_total
    return render_template('portfolio.html', companies=session["portfolio"], conversion=conversion_rates, total_value=total_value, custom_accounts=custom_accounts)



@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user_login = request.form["user_login"]
        password = request.form["user_pass"]
        error = check_login_details(user_login, password)
        if (error):
            flash(error, "danger")
            return redirect('/login')
        if request.form.get("remember_me"):
            store_session(user_login, True)
        else:
            store_session(user_login, False)
        return redirect('/')
    elif request.method == "GET":
        return render_template("login.html")
    #if user is logged in

@app.route('/signup', methods=["GET", "POST"])
def signup():

    if request.method == "POST":
        username = request.form["user_name"]
        email = request.form["user_email"]
        password = request.form["user_pass"]
        password_conf = request.form["user_pass_conf"]
        error = check_signup_details(username, email, password, password_conf)

        if (error):
            flash(error, "danger")
            return redirect('/signup')

        #checks password from form against password against stored user password in database
        hash = generate_password_hash(password, method='pbkdf2:sha256', salt_length=8)
        #creates user model then adds to database
        get_db().execute("INSERT INTO users (username, email, hash) VALUES (?, ?, ?)", (username, email, hash, ))
        get_db().commit()
        store_session(username, False)
        return render_template("index.html")
    elif request.method == "GET":
        return render_template("signup.html")

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

def getsearchlist(search_term):
    #yahoo search endpoint
    url = "https://query2.finance.yahoo.com/v1/finance/search"
    #yahoo search endpoint params - limited to 7 results??
    params = {'q': search_term, 'quotesCount': 7, 'newsCount': 0}
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:93.0) Gecko/20100101 Firefox/93.0'}
    #grabs request
    r = requests.get(url, params=params, headers=headers)
    #converts json to python object (useful info in quotes)
    data = r.json()
    #grab watchlist from DB
    watchlist = get_watchlist()
    portfolio = get_portfolio()
    session["search_term"] = search_term

    #pulls watchlist and portfolio list and creates datalist and stores in user session
    for company in data["quotes"]:
        for watched in watchlist:
            if company["symbol"] == watched["symbol"]:
                company["watchlist"] = True
        for iportfolio in portfolio:
            if company["symbol"] == iportfolio["symbol"]:
                company["portfolio"] = True
    if search_term == '':
        session["last_search"] = None
    else:
        session["last_search"] = data["quotes"]

if __name__ == '__main__':
    import os
    HOST = os.environ.get('SERVER_HOST', 'localhost')
    try:
        PORT = int(os.environ.get('SERVER_PORT', '5555'))
    except ValueError:
        PORT = 5555
    app.run(HOST, PORT)
