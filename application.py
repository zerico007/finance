import os

from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd
import datetime
import itertools

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")

# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")


@app.route("/")
@login_required
def index():
    lines = db.execute("SELECT symbol, name, shares FROM user_portfolio WHERE Id = :Id", Id = session["user_id"])
    user = db.execute("SELECT * FROM users WHERE Id = :Id", Id= session["user_id"])
    username = user[0]["username"]
    usd_cash = usd(user[0]["cash"])

    count = db.execute("SELECT Id, COUNT(symbol) FROM user_portfolio GROUP BY Id HAVING Id = :Id", Id = session["user_id"])

    lines = db.execute("SELECT * FROM user_portfolio WHERE Id = :Id", Id = session["user_id"])
    stocks = []
    lookups = []
    prices = []
    shares = []
    values = []
    int_values = []

    if count == []:
        table_count = 0
    else:
        table_count = count[0]["COUNT(symbol)"]

        for i in range(count[0]["COUNT(symbol)"]):
            stocks.append(lines[i]["symbol"])

        for j in range (count[0]["COUNT(symbol)"]):
            lookups.append(lookup(stocks[j]))

        for k in range (count[0]["COUNT(symbol)"]):
            prices.append(usd(lookups[k]["price"]))

        for m in range(count[0]["COUNT(symbol)"]):
            shares.append(lines[m]["shares"])

        for n in range(count[0]["COUNT(symbol)"]):
            values.append(usd(lookups[n]["price"] * shares[n]))

        for o in range(count[0]["COUNT(symbol)"]):
            int_values.append(lookups[o]["price"] * shares[o])

    Sum = usd(sum(int_values) + user[0]["cash"])

    return render_template("index.html", username=username, usd_cash=usd_cash, prices=prices, lines=lines, values=values, table_count=table_count, Sum=Sum)


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    if request.method == "POST":
        if not request.form.get("symbol"):
            return apology("input stock symbol", 403)
        if not request.form.get("shares"):
            return apology("input number of shares requested", 403)
        buy_search = lookup(request.form.get("symbol"))
        if buy_search == None:
           return apology("stock symbol not found", 403)

        bought_shares = int(request.form.get("shares"))
        buy_cost = float(buy_search["price"] * bought_shares)

        rows = db.execute("SELECT * FROM users WHERE Id = :Id",
                Id = session["user_id"])
        if rows[0]["cash"] < buy_cost:
            return apology("buy order exceeds available cash")
        remaining_cash = float(rows[0]["cash"] - buy_cost)

        db.execute("UPDATE users SET cash = :cash WHERE Id = :Id", cash=remaining_cash, Id = session["user_id"])
        new_rows = db.execute("SELECT * FROM users WHERE Id = :Id",
                Id = session["user_id"])
        cash_usd = usd(new_rows[0]["cash"])
        db.execute("INSERT INTO buy_transactions (transacted, symbol, shares, price, name, cash, transaction_amount, Id) VALUES (:transacted, :symbol, :shares, :price, :name, :cash, :transaction_amount, :Id)",
                    transacted=datetime.datetime.now(), symbol=request.form.get("symbol"), shares=bought_shares, price=usd(buy_search["price"]), cash=usd(remaining_cash), name=buy_search["name"], transaction_amount=usd(buy_cost), Id=session["user_id"])

        db.execute("INSERT INTO transactions (transacted, symbol, shares, price, name, Id) VALUES (:transacted, :symbol, :shares, :price, :name, :Id)",
                    transacted=datetime.datetime.now(), symbol=request.form.get("symbol"), shares=bought_shares, price=usd(buy_search["price"]), name=buy_search["name"], Id=session["user_id"])

        update = db.execute("SELECT * from user_portfolio WHERE Id = :Id AND symbol = :symbol",
                    Id = session["user_id"], symbol=request.form.get("symbol"))
        if len(update) == 0:
            db.execute("INSERT INTO user_portfolio (Id, symbol, name, shares) VALUES (:Id, :symbol, :name, :shares)",
                Id=session["user_id"], symbol=request.form.get("symbol"), name=buy_search["name"], shares=request.form.get("shares"))

        elif len(update) == 1:
            new_shares = update[0]["shares"] + int(request.form.get("shares"))

            db.execute("UPDATE user_portfolio SET shares = :shares WHERE Id = :Id AND symbol = :symbol",
                    shares=new_shares, Id = session["user_id"], symbol=request.form.get("symbol"))

        updated = db.execute("SELECT * from user_portfolio WHERE Id = :Id AND symbol = :symbol",
                    Id = session["user_id"], symbol=request.form.get("symbol"))


        lines = db.execute("SELECT symbol, name, shares FROM user_portfolio WHERE Id = :Id", Id = session["user_id"])

        user = db.execute("SELECT * FROM users WHERE Id = :Id", Id= session["user_id"])


        count = db.execute("SELECT Id, COUNT(symbol) FROM user_portfolio GROUP BY Id HAVING Id = :Id", Id = session["user_id"])

        lines = db.execute("SELECT * FROM user_portfolio WHERE Id = :Id", Id = session["user_id"])
        stocks = []
        lookups = []
        prices = []
        shares = []
        values = []
        int_values = []

        table_count = count[0]["COUNT(symbol)"]

        for i in range(count[0]["COUNT(symbol)"]):
            stocks.append(lines[i]["symbol"])

        for j in range (count[0]["COUNT(symbol)"]):
            lookups.append(lookup(stocks[j]))

        for k in range (count[0]["COUNT(symbol)"]):
            prices.append(usd(lookups[k]["price"]))

        for m in range(count[0]["COUNT(symbol)"]):
            shares.append(lines[m]["shares"])

        for n in range(count[0]["COUNT(symbol)"]):
            values.append(usd(lookups[n]["price"] * shares[n]))

        for o in range(count[0]["COUNT(symbol)"]):
            int_values.append(lookups[o]["price"] * shares[o])

        Sum = usd(sum(int_values) + new_rows[0]["cash"])

        return render_template("bought.html", lines=lines, cash_usd=cash_usd,prices=prices, values=values, table_count=table_count, Sum=Sum)
    else:
        return render_template("buy.html")


@app.route("/history")
@login_required
def history():

    lines = db.execute("SELECT * FROM transactions WHERE Id = :Id", Id = session["user_id"])

    return render_template("history.html", lines=lines)

@app.route("/buy_history")
@login_required
def buy_history():

    lines = db.execute("SELECT * FROM buy_transactions WHERE Id = :Id", Id = session["user_id"])

    return render_template("buy_history.html", lines=lines)

@app.route("/sell_history")
@login_required
def sell_history():

    lines = db.execute("SELECT * FROM sell_transactions WHERE Id = :Id", Id = session["user_id"])

    return render_template("sell_history.html", lines=lines)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["Hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["Id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    if request.method == "POST":
       search = lookup(request.form.get("symbol"))
       if search == None:
           return apology("stock symbol not found", 403)
       usdPrice = usd(search["price"])
       return render_template("quoted.html", search=search, usdPrice=usdPrice)

    else:
        return render_template("quote.html")




@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        if not request.form.get("username"):
            return apology("must provide username", 403)

        elif not request.form.get("password"):
            return apology("must provide password", 403)

        elif not request.form.get("confirmation"):
            return apology("please retype password", 403)

        elif request.form.get("password") != request.form.get("confirmation"):
            return apology("passwords do not match", 403)

        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))
        if len(rows) == 1:
            return apology("Username already exists", 403)

        Hash = generate_password_hash(request.form.get("password"))

        username = request.form.get("username")

        db.execute("INSERT INTO users (username, hash) VALUES (:username, :Hash)", username=username, Hash=Hash)
        db.execute("INSERT INTO user_portfolio (username) VALUES (:username)", username=username)
        return redirect("/")

    else:
        return render_template("register.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    if request.method == "POST":

        if not request.form.get("shares"):
            return apology("input number of shares to sell", 403)
        sell_search = lookup(request.form.get("symbol"))
        sold_shares = int(request.form.get("shares"))
        sell_cost = float(sell_search["price"] * sold_shares)
        checks = db.execute("SELECT * FROM buy_transactions WHERE Id = :Id AND symbol = :symbol",
                    Id = session["user_id"], symbol = request.form.get("symbol"))
        if len(checks) == 0:
            return apology("You do not own this stock", 403)

        shares_owned = db.execute("SELECT SUM(shares) FROM buy_transactions WHERE Id = :Id AND symbol = :symbol",
                    Id = session["user_id"], symbol = request.form.get("symbol"))

        shares_owned_total = shares_owned[0]["SUM(shares)"]

        if sold_shares > shares_owned_total:
             return apology("You do not own that many shares of this stock", 403)

        rows = db.execute("SELECT * FROM users WHERE Id = :Id",
                Id = session["user_id"])
        remaining_cash = float(rows[0]["cash"] + sell_cost)

        db.execute("UPDATE users SET cash = :cash WHERE Id = :Id", cash=remaining_cash, Id = session["user_id"])
        new_rows = db.execute("SELECT * FROM users WHERE Id = :Id",
                Id = session["user_id"])
        cash_usd = usd(new_rows[0]["cash"])
        db.execute("INSERT INTO sell_transactions (transacted, symbol, shares, price, name, cash, transacted_amount, Id) VALUES (:transacted, :symbol, :shares, :price, :name, :cash, :transacted_amount, :Id)",
                    transacted=datetime.datetime.now(), symbol=request.form.get("symbol"), shares=(-sold_shares), price=usd(sell_search["price"]), cash=usd(remaining_cash), name=sell_search["name"], transacted_amount=usd(sell_cost), Id=session["user_id"])

        db.execute("INSERT INTO transactions (transacted, symbol, shares, price, name, Id) VALUES (:transacted, :symbol, :shares, :price, :name, :Id)",
                    transacted=datetime.datetime.now(), symbol=request.form.get("symbol"), shares=(-sold_shares), price=usd(sell_search["price"]), name=sell_search["name"], Id=session["user_id"])

        update = db.execute("SELECT * from user_portfolio WHERE Id = :Id AND symbol = :symbol",
                    Id = session["user_id"], symbol=request.form.get("symbol"))
        if len(update) == 0:
            return apology("YOu do not own this stock", 403)

        elif len(update) == 1:
            new_shares = update[0]["shares"] - int(request.form.get("shares"))

            db.execute("UPDATE user_portfolio SET shares = :shares WHERE Id = :Id AND symbol = :symbol",
                    shares=new_shares, Id = session["user_id"], symbol=request.form.get("symbol"))
            db.execute("DELETE FROM user_portfolio WHERE shares = 0")

        updated = db.execute("SELECT * from user_portfolio WHERE Id = :Id AND symbol = :symbol",
                    Id = session["user_id"], symbol=request.form.get("symbol"))

        lines = db.execute("SELECT symbol, name, shares FROM user_portfolio WHERE Id = :Id", Id = session["user_id"])

        user = db.execute("SELECT * FROM users WHERE Id = :Id", Id= session["user_id"])


        count = db.execute("SELECT Id, COUNT(symbol) FROM user_portfolio GROUP BY Id HAVING Id = :Id", Id = session["user_id"])

        lines = db.execute("SELECT * FROM user_portfolio WHERE Id = :Id", Id = session["user_id"])
        stocks = []
        lookups = []
        prices = []
        shares = []
        values = []
        int_values = []

        table_count = count[0]["COUNT(symbol)"]

        for i in range(count[0]["COUNT(symbol)"]):
            stocks.append(lines[i]["symbol"])

        for j in range (count[0]["COUNT(symbol)"]):
            lookups.append(lookup(stocks[j]))

        for k in range (count[0]["COUNT(symbol)"]):
            prices.append(usd(lookups[k]["price"]))

        for m in range(count[0]["COUNT(symbol)"]):
            shares.append(lines[m]["shares"])

        for n in range(count[0]["COUNT(symbol)"]):
            values.append(usd(lookups[n]["price"] * shares[n]))

        for o in range(count[0]["COUNT(symbol)"]):
            int_values.append(lookups[o]["price"] * shares[o])

        Sum = usd(sum(int_values) + new_rows[0]["cash"])

        return render_template("sold.html", lines=lines, cash_usd=cash_usd, prices=prices, values=values, table_count=table_count, Sum=Sum)
    else:
        lines = db.execute("SELECT * FROM user_portfolio WHERE Id = :Id", Id = session["user_id"])
        return render_template("sell.html", lines=lines)


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
