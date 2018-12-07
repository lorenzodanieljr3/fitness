import os
import csv

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
    """Show list of workouts"""

    user = session["user_id"]

    data = db.execute("SELECT * FROM users WHERE id=:current", current=user)


    for line in data:
        # line["name"] = name

    # Render portfolio
        return render_template("home.html")

@app.route("/home")
@login_required
def home():
    """Show homepage"""

    return render_template("home.html")


@app.route("/gyms", methods=["GET", "POST"])
@login_required
def gyms():
    googlemap = "https://www.google.com/maps/embed/v1/search?q=gyms%20near%20dallas&key=AIzaSyBe1qKb3dtLyIWxdHPgftdhBZi84Cd5EyI"

    if request.method == "POST":
        city=request.form.get("city")
        googlemap = googlemap.replace("dallas", str(city))

    return render_template("gyms.html", googlemap=googlemap)

@app.route("/guide")
@login_required
def guide():
    """Show workout tips, guide, diet, meal plans"""

    return render_template("guide.html")


@app.route("/profile", methods=["GET","POST"])
@login_required
def profile():
    """Show profile"""
    if request.method == "GET":
        return render_template("profile.html")

    if request.method == "POST":
        return render_template("workout1.html")


@app.route("/challenge")
@login_required
def challenge():
    """Show challenges"""

    return render_template("challenge.html")

# @app.route("/calories")
# @login_required
# def calories():
#     """Calorie Calculator"""

#     return render_template("calories.html")

@app.route("/workout")
@login_required
def workout():
    return render_template("workout.html")

@app.route("/workout1")
@login_required
def workout1():
    return render_template("workout1.html")


@app.route("/workout2")
@login_required
def workout2():
    return render_template("workout2.html")

@app.route("/workouta")
@login_required
def workouta():
    return render_template("workouta.html")

@app.route("/workoutb")
@login_required
def workoutb():
    return render_template("workoutb.html")



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
        return redirect("/home")

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
        return redirect("/")

    else:
        return render_template("register.html")

@app.route("/form", methods=["GET"])
def get_form():
    return render_template("workout.html")


@app.route("/form", methods=["POST"])
def post_form():

    # Open csv file and write information from the form into the sheet
    with open("workoutlog.csv", "a") as file:
        data = csv.writer(file)
        data.writerow((request.form.get("name"), request.form.get("type"), request.form.get("distance"), request.form.get("duration"), request.form.get("time")))
    return redirect("/log")


@app.route("/log", methods=["GET"])
def get_sheet():
    # Open sheet with table from sheet.html
    with open("workoutlog.csv", "r") as file:
        read = csv.reader(file)
        athletes = list(read)
    return render_template("log.html", athletes=athletes)