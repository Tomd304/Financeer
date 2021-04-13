"""
This script runs the application using a development server.
It contains the definition of routes and views for the application.
"""

from flask import Flask, render_template, session, request, flash, redirect, g
from werkzeug.security import generate_password_hash, check_password_hash
from helpers import password_check, login_required, get_db, query_db, check_signup_details, check_login_details, store_session, watchlist_add, get_watchlist, get_prices, watchlist_remove
from helpers import currency, percentage
from datetime import timedelta
import sqlite3, yfinance as yf, requests, json
#from yfinance_help import ticker_info_dict



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


@app.route('/search', defaults={'ticker' : None}, methods=["GET", "POST"])
@app.route('/search/<ticker>')
def search(ticker):
    if request.method == "POST":
        if ("search" in request.form):
            #grabs search term from search bar
            search_term = request.form["search"]
            #yahoo search endpoint
            url = "https://query2.finance.yahoo.com/v1/finance/search"
            #yahoo search endpoint params - limited to 7 results??
            params = {'q': search_term, 'quotesCount': 7, 'newsCount': 0}
            #grabs request
            r = requests.get(url, params=params)
            #converts json to python object (useful info in quotes)
            data = r.json()
            #grab watchlist from DB
            watchlist = get_watchlist()
            for watched in watchlist:
                for company in data["quotes"]:
                    if company["symbol"] in watched["symbol"]:
                        company["watchlist"] = True
            if search_term == '':
                session["last_search"] = None
            else:
                session["last_search"] = data["quotes"]
            return render_template("search.html", data = session["last_search"])
        elif ("watch" in request.form):
            watchlist_add(request.form['watch'])
            for i in range(len(session["last_search"])):
                if (session["last_search"][i]["symbol"] == request.form['watch']):
                    session["last_search"][i]["watchlist"] = True
                    session["last_search"] = session["last_search"]
            #for company in session["last_search"]:
            #    if (company["symbol"] == request.form['watch']):
            #        company["watchlist"] = True
            return render_template("search.html", data = session["last_search"])
        elif ("removewatch" in request.form):
            watchlist_remove(request.form['removewatch'])

            for i in range(len(session["last_search"])):
                if (session["last_search"][i]["symbol"] == request.form['removewatch']):
                    session["last_search"][i]["watchlist"] = None
                    session["last_search"] = session["last_search"]

            #for company in session["last_search"]:
            #    if (company["symbol"] == request.form['removewatch']):
            #        company["watchlist"] = None
            return render_template("search.html", data = session["last_search"])     


@app.route('/stock', defaults={'ticker' : None}, methods=["GET", "POST"])
@app.route('/stock/<ticker>', methods=["GET", "POST"])
def stock(ticker):

    if request.method == "POST":
        if "watch" in request.form:
            watchlist_add(ticker)
        elif "removewatch" in request.form:
            watchlist_remove(ticker)
    if ticker:
        company = yf.Ticker(ticker).info
        price = yf.Ticker(ticker).history(period='7d')["Close"]
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
            print(session["watchlist"])
            for i in range(len(session["watchlist"])):
                if (session["watchlist"][i]["symbol"] == request.form['removewatch']):
                    del session["watchlist"][i]
                    session["watchlist"] = session["watchlist"]
                    break
            print(session["watchlist"])
            return render_template('watchlist.html', companies=session["watchlist"])   
    elif request.method == "GET":
        info = get_watchlist()
        dict = get_prices(info)
        session["watchlist"] = dict
        return render_template('watchlist.html', companies=session["watchlist"])




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



if __name__ == '__main__':
    import os
    HOST = os.environ.get('SERVER_HOST', 'localhost')
    try:
        PORT = int(os.environ.get('SERVER_PORT', '5555'))
    except ValueError:
        PORT = 5555
    app.run(HOST, PORT)
