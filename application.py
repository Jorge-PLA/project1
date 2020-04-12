import os
import requests
import simplejson as json
from flask import Flask, session, request, render_template, redirect, url_for, jsonify
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from werkzeug.security import check_password_hash, generate_password_hash
from helpers import login_required


app = Flask(__name__)


# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))


@app.route("/")
def index():
    return render_template("index.html")

@app.route("/register", methods=["GET", "POST"])
def register():

    #Forget any user id
    session.clear()

    if request.method == "GET":
        return render_template("register.html")

    else:

         # Ensure username was submitted
        if not request.form.get("username"):
            message = "Invalid Username"
            return render_template("mistake.html", message = "Invalid username" )

        # Ensure password was submitted
        elif not request.form.get("password"):
            return render_template("mistake.html", message = "invalid password")

        # Ensure confirmed password was submitted
        elif not request.form.get("password2"):
            return render_template("mistake.html", message = "confirm password")

        # Ensure confirmed password and password are the same
        elif request.form.get("password") != request.form.get("password2"):
            return render_template("mistake.html", message = "password did´nt match")

        # Query database for username
        username = request.form.get("username")
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          {"username": username}).fetchall()

        # Ensure username not exists
        if len(rows) == 1:
            return render_template("mistake.html", message = "invalid username, try other")

        # Ensure password is at least 8 characters
        password = request.form.get("password")
        if len(password) < 8:
            return render_template("mistake.html", message = "Use at least 8 characters for password")
        # Ensure has letters and numbers
        if (not any(str.isdigit(c) for c in password)) or (not any(str.isalpha(d) for d in password)):
            return render_template("mistake.html", message = "use letters and numbers in your password")

        # Generate a hash and submit it and username in the database
        ha = generate_password_hash(request.form.get("password"))
        username = request.form.get("username")
        db.execute("INSERT INTO users (username, hash) VALUES (:username, :ha)", {"username": username, "ha": ha})
        user = db.execute("SELECT user_id FROM users WHERE username = :username", {"username": username}).fetchone()

        # Remember which user has logged in
        session["user_id"] = user.user_id

        db.commit()

        # Redirect user to home page
        return render_template("search.html")

@app.route("/login", methods=["GET", "POST"])
def login():

    # Forget any user_id
    session.clear()

    if request.method == "GET":
        return render_template("login.html")

    else:

        # Ensure username was submitted
        if not request.form.get("username"):
            return render_template("mistake.html", message = "Invalid username")

        # Ensure password was submitted
        elif not request.form.get("password"):
            return render_template("mistake.html", message = "Invalid password")

        username = request.form.get("username")
        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          {"username":username}).fetchall()

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0].hash, request.form.get("password")):
            return render_template("mistake.html", message = "invalid username and/or password")

        # Remember which user has logged in
        session["user_id"] = rows[0].user_id

        # Redirect user to search page
        return redirect("/search")


@app.route("/search", methods=["GET", "POST"])
@login_required
def search():


    if request.method == "GET":
        return render_template("search.html")

    else:

        word = request.form.get("word")

        # check if the word has a similarity with title, author or ISBN
        results = db.execute("SELECT title, author, isbn FROM books WHERE LOWER(title) LIKE LOWER(:word) OR LOWER(author) LIKE LOWER(:word) OR isbn LIKE :word", {"word": '%' + word + '%', "word": '%' + word + '%', "word": '%' + word + '%'}).fetchall()

        if len(results) == 0:
            return render_template("mistake.html", message = "No search found")

        else:
            return render_template("searched.html", results = results)

@app.route("/book/<string:isbn>", methods=["GET", "POST"])
@login_required
def book(isbn):
    KEY ="yIl0C8oLijxjhSlwt60eA"
    isbn = isbn
    # Get data from the API goodreads
    res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": KEY, "isbns": isbn})

    # Check API request
    if res.status_code != 200:
        raise Exception("ERROR: API request unsuccessful.")

    # turn res in json data
    apijson = res.json()
    api = apijson['books'][0]

    if request.method == "GET":

        book = db.execute("SELECT * FROM books WHERE isbn = :isbn", {"isbn": isbn}).fetchone()
        rev = db.execute("SELECT review_rate, review, username FROM reviews JOIN users ON users.user_id = reviews.id_user WHERE id_book in (SELECT id_book FROM books WHERE isbn = :isbn)", {"isbn": isbn}).fetchall()
        data = db.execute("SELECT ROUND(AVG(review_rate),2) AS avg, COUNT(review_rate) AS counter FROM reviews WHERE id_book in (SELECT id_book FROM books WHERE isbn = :isbn)", {"isbn": isbn}).fetchone()

        return render_template("book.html", api = api, book = book, rev = rev, data = data)

    else:

        # Get data from forms
        rate = int(request.form.get("rating"))
        review = request.form.get("opinion")

        book = db.execute("SELECT * FROM books WHERE isbn = :isbn", {"isbn": isbn}).fetchone()
        id_book = book.id_book

        check = db.execute("SELECT id_user FROM reviews JOIN users ON users.user_id = reviews.id_user WHERE id_book in (SELECT id_book FROM books WHERE isbn = :isbn)", {"isbn": isbn}).fetchall()

        if len(check) >= 1:
            return render_template("mistake.html", message = "you can only give one review per book")
        # Insert reviews in db

        db.execute("INSERT INTO reviews (id_user, review, review_rate, id_book) VALUES (:id_user, :review, :review_rate, :id_book)", {"id_user": session["user_id"], "review": review, "review_rate": rate, "id_book": id_book })

        db.commit()

        return '', 204

@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")

@app.route("/api/<string:isbn>")
def bookbe_api(isbn):
    """Return details about books of bookbe."""

    # Make sure the book exists
    book = db.execute("SELECT * FROM books WHERE isbn = :isbn", {"isbn": isbn}).fetchone()
    if book is None:
        return jsonify({"error": "Not found"}), 404
    data = db.execute("SELECT  ROUND(AVG(review_rate),2) AS avg, COUNT(review_rate) AS counter FROM reviews WHERE id_book in (SELECT id_book FROM books WHERE isbn = :isbn)", {"isbn": isbn}).fetchone()

    return jsonify({
        "title": book.title,
        "author": book.title,
        "year": book.year,
        "isbn": book.isbn,
        "review_count": data.counter,
        "average_score": data.avg
    })
