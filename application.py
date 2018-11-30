import os

from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session, url_for
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions
from werkzeug.security import check_password_hash, generate_password_hash
from passlib.context import CryptContext

from helpers import apology, login_required, lookup, usd

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
db = SQL("sqlite:///fitness.db")


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""

    user = session["user_id"]

    data = db.execute("SELECT symbol FROM purchases WHERE purchaser=:current GROUP BY symbol", current=user)

    summed = db.execute("SELECT symbol, SUM(shares) FROM purchases WHERE purchaser=:current GROUP BY symbol", current=user)

    index = 0
    counter = 0

    for line in data:
        look = lookup(line["symbol"])
        line["sum"] = summed[index]["SUM(shares)"]
        line["symbol"] = look["symbol"]
        line["price"] = (look["price"])
        line["total"] = (line["price"] * line["sum"])
        counter += (line["price"] * line["sum"])
        index = index + 1

    cash = db.execute("SELECT cash FROM users WHERE id=:login_id", login_id=session["user_id"])
    money = cash[0]["cash"]

    grandtotal = money + counter
    GrandTotal = usd(grandtotal)
    Money = usd(money)

    return render_template("index.html", data=data, Money=Money, GrandTotal=GrandTotal)


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    if request.method == "POST":
        # check if valid input
        try:
            symbol = lookup(request.form.get("symbol"))
            shares = int(request.form.get("shares"))
        except:
            return apology("enter some input")

        # if symbol is empty return apology
        if not symbol:
            return apology("enter a valid symbol")

        # if shares is empty
        if not shares or shares <= 0:
            return apology("enter the quantity of shares")

        # if can't afford to buy then error
        # get cash from db
        total_amount = (shares) * symbol["price"]
        current_user_amount = db.execute("SELECT cash FROM users WHERE id = :id", id=session["user_id"])
        remainder = current_user_amount[0]["cash"] - total_amount
        typeoftransaction = "BUY"

        if remainder < 0:
            return apology("Not enough money")
        else:
            db.execute("UPDATE users SET cash = :remainder WHERE id = :id", id=session["user_id"], remainder=remainder)

            db.execute("""INSERT INTO purchases (purchaser, symbol, shares, price_of_stock, total_purchase_price, typeoftransaction)
                VALUES(:purchaser, :symbol, :shares, :price_of_stock, :total_purchase_price, :typeoftransaction)""",
                       purchaser=session["user_id"], symbol=symbol["symbol"], shares=shares, price_of_stock=symbol["price"], total_purchase_price=total_amount, typeoftransaction=typeoftransaction)

        flash("Bought!")

        return redirect(url_for("index"))

    else:
        return render_template("buy.html")


@app.route("/check", methods=["GET"])
def check():
    """Return true if username available, else false, in JSON format"""
    check = request.args.get("username")
    look = db.execute("SELECT * FROM users WHERE username =:current", current=check)
    if not len(check) or look:
        return jsonify(False)
    else:
        return jsonify(True)


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""

    currentuser = session["user_id"]

    data = db.execute("SELECT * FROM purchases WHERE purchaser=:current", current=currentuser)

    for line in data:
        line["price"] = usd(line["price_of_stock"])

    return render_template("history.html", data=data)


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
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

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
    """Get stock quote."""
    if request.method == "POST":
        quote = lookup(request.form.get("symbol"))
        if not quote:
            return apology("stock not found")
        else:
            quote['price'] = usd(quote['price'])
            return render_template("quote.html", quote=quote)
    else:
        return render_template("quote.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    # manipulate the information the user has submitted
    if request.method == "POST":

        # ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username")

        # ensure password was submitted
        if not request.form.get("password"):
            return apology("must provide password")

        # ensure password confirmation was submitted
        if not request.form.get("confirmation"):
            return apology("must provide password confirmation")

        # ensure password and confirmation match
        if request.form.get("password") != request.form.get("confirmation"):
            return apology("passwords must match")

        # store the hash of the password and not the actual password that was typed in
        hashp = generate_password_hash(request.form.get("password"))

        # username must be a unique field
        result = db.execute("INSERT INTO users (username, hash) VALUES (:username, :hash)",
                            username=request.form.get("username"), hash=hashp)
        if not result:
            return apology("pick a different username")

        # store their id in session to log them in automatically
        user_id = db.execute("SELECT id FROM users WHERE username = :username", username=request.form.get("username"))
        session["user_id"] = user_id[0]["id"]
        return redirect(url_for("index"))

    else:
        return render_template("register.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""

    user = session["user_id"]
    data = db.execute("SELECT symbol FROM purchases WHERE purchaser=:current", current=user)
    seller = set(val for dic in data for val in dic.values())

    for line in seller:
        line

    if request.method == "POST":

        symbol = lookup(request.form.get("symbol"))
        typeoftransaction = "SELL"

        if (symbol) == None:
            return apology("No such symbol")

        # Check if shares was a positive integer
        try:
            shares = int(request.form.get("shares"))
        except:
            return apology("shares must be a positive integer", 400)

            # Check if # of shares requested was 0
        if shares <= 0:
            return apology("can't sell less than or 0 shares", 400)

        currentuser = session["user_id"]

        stock = db.execute("SELECT SUM(shares) as total_shares FROM purchases WHERE purchaser= :current AND symbol = :symbol GROUP BY symbol",
                           current=currentuser, symbol=request.form.get("symbol"))

        if len(stock) != 1 or stock[0]["total_shares"] <= 0 or stock[0]["total_shares"] < shares:
            return apology("you can't sell less than 0 or more than you own", 400)

        rows = db.execute("SELECT cash FROM users WHERE id = :current", current=currentuser)

        # Calculate the price of requested shares
        price_of_stock = symbol["price"]
        total_price = price_of_stock * int(shares)

        # Book keeping (TODO: should be wrapped with a transaction)
        db.execute("UPDATE users SET cash = cash + :price WHERE id =:current", price=total_price, current=currentuser)
        db.execute("INSERT INTO purchases (purchaser, symbol, shares, price_of_stock, typeoftransaction) VALUES(:purchaser, :symbol, :shares, :price_of_stock, :typeoftransaction)",
                   purchaser=session["user_id"], symbol=symbol["symbol"], shares=-shares, price_of_stock=symbol["price"], typeoftransaction=typeoftransaction)

        flash("Sold!")

        return redirect(url_for("index"))
    else:
        return render_template("sell.html", seller=seller)


@app.route("/loan", methods=["GET", "POST"])
@login_required
def loan():
    """Get a loan."""

    if request.method == "POST":

        # ensure must be integers
        try:
            loan = int(request.form.get("loan"))
            if loan < 0:
                return apology("Loan must be positive amount")
            elif loan > 1000:
                return apology("Cannot loan more than $1,000 at once")
        except:
            return apology("Loan must be positive integer")

        currentuser = session["user_id"]
        # update user cash (increase)
        db.execute("UPDATE users SET cash = cash + :loan WHERE id = :current", loan=loan, current=currentuser)

        flash("Success!")

        return redirect(url_for("index"))
    else:
        return render_template("loan.html")


def errorhandler(e):
    """Handle error"""
    return apology(e.name, e.code)


 # listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
