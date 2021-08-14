import os

from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash


from helpers import apology, login_required


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
# jinja is needed for parsing {{ variables }} into html so htmls can be generated dynamically
# {% block main/title/etc. %} demarcated a block start and {% endblock %}
# this is what iterating over a table might look like in the html template
"""{% for row in rows %}
                    <tr>
                        <th>{{ row["symbol"] }}</th>
                        <th>{{ row["name"] }}</th>
                        <th>{{ row["shares"] }}</th>
                        <th>{{ row["cost"] }}</th>
                        <th>{{ row["balance"] }}</th>
                        <th>{{ row["timestamp"] }}</th>
                    </tr>
                    {% endfor %}"""
# app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///movies.db")
"""Schema for SQL database from finance.db
CREATE TABLE IF NOT EXISTS 'users' ('id' INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, 'username' TEXT NOT NULL, 'hash' TEXT NOT NULL, 'cash' NUMERIC NOT NULL DEFAULT 10000.00 );
CREATE TABLE sqlite_sequence(name,seq);
CREATE UNIQUE INDEX 'username' ON "users" ("username");
CREATE TABLE IF NOT EXISTS 'transactions' ('id' INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, 'user_id' NUMERIC NOT NULL, 'symbol' TEXT NOT NULL, 'shares' NUMERIC NOT NULL, 'cost' NUMERIC, 'balance' NUMERIC NOT NULL, 'timestamp' DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS 'stocks' ('id' INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, 'user_id' NUMERIC NOT NULL, 'symbol' TEXT NOT NULL, 'totalshares' NUMERIC NOT NULL);
CREATE TABLE IF NOT EXISTS 'deposits' ('id' INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, 'user_id' NUMERIC NOT NULL, 'deposit' NUMERIC NOT NULL, 'timestamp' DEFAULT CURRENT_TIMESTAMP);"""

# # Make sure API key is set (not needed for movie database)
# if not os.environ.get("API_KEY"):
#     raise RuntimeError("API_KEY not set")

@app.route("/")
@login_required
def function():
    return redirect("/index")
    
    
@app.route("/index")
@login_required
def index():
    """Show portfolio of your rated Movies"""
    # get every entry from the user in usermovies (as in what they rated at that moment)
    rows = db.execute("SELECT * FROM usermovies JOIN movies ON usermovies.movie_id = movies.id JOIN ratings ON usermovies.movie_id = ratings.movie_id WHERE user_id = :user_id ORDER BY DATE(timestamp) DESC, TIME(timestamp) DESC", user_id = session["user_id"])
    # adding timestamp to the table
    for row in rows:
        timestamp = row["timestamp"].split()
        row["day"] = timestamp[0]
    # passing some arguments to index.html so it can handle the different variables -> going to index.html
    return render_template("index.html", rows = rows)


@app.route("/select", methods = ["GET", "POST"])
@login_required
def select():
    """Returns list of movies in select.html from search querie in new.html."""
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # gets inputs from form in new.html
        titleraw = request.form.get("title").rstrip()
        directorraw = request.form.get("director").rstrip()
        # so that it can be used with "LIKE" in sql query
        title = f"%{titleraw}%"
        director = f"%{directorraw}%"
        # logic to check which fields input was provided to
        try:
            year = int(request.form.get("year"))
            if year < 1970:
                flash('Sorry, only movies from 1970 onwards.')
                return redirect('/new')
                # return apology("only movies from 1970 onwards", 403)
            rows = db.execute("SELECT *, GROUP_CONCAT(name, ', ') as directors FROM movies LEFT JOIN directors ON movies.id = directors.movie_id JOIN people ON directors.person_id = people.id JOIN ratings ON movies.id = ratings.movie_id WHERE title LIKE :title AND year = :year AND name LIKE :director GROUP BY movies.id LIMIT (100)", title = title, year = year, director = director)
        except:
            if len(titleraw) == 0 and len(directorraw) == 0:
                flash('Please input search items.')
                return redirect('/new')
            rows = db.execute("SELECT *, GROUP_CONCAT(name, ', ') as directors FROM movies LEFT JOIN directors ON movies.id = directors.movie_id JOIN people ON directors.person_id = people.id JOIN ratings ON movies.id = ratings.movie_id WHERE title LIKE :title AND name LIKE :director GROUP BY movies.id LIMIT (100)", title = title, director = director)
        if len(rows) == 0:
            flash('Sorry, no such movie found.')
            return redirect('/new')
        else:
            # this is to see whether the movie is in wl or movies already -> if so update button is presented in select.html instead of rate and +watchlist button
            for row in rows:
                id = row["movie_id"]
                # just as a little indicator to check in html with jinja {{ present? }}
                present = db.execute("SELECT * FROM usermovies WHERE movie_id = :id AND user_id = :user_id", id = id, user_id = session["user_id"])
                presentwl = db.execute("SELECT * FROM watchlist WHERE movie_id = :id AND user_id = :user_id", id = id, user_id = session["user_id"])
                row["present"] = len(present)
                row["presentwl"] = len(presentwl)
            # title present
            if len(titleraw) != 0:
                # director present or not
                if len(directorraw) != 0:
                    # try always with year, except without year
                    try:
                        return render_template("select.html", rows = rows, title = titleraw, year = year, director = directorraw)
                    except:
                        return render_template("select.html", rows = rows, title = titleraw, director = directorraw)
                else:
                    try:
                        return render_template("select.html", rows = rows, title = titleraw, year = year)
                    except:
                        return render_template("select.html", rows = rows, title = titleraw)
            # director present
            elif len(directorraw) != 0:
                try:
                    return render_template("select.html", rows = rows, year = year, director = directorraw)
                except:
                    return render_template("select.html", rows = rows, director = directorraw)
            else:
                # only year is given in this case
                return render_template("select.html", rows = rows, year = year)


@app.route("/new", methods = ["GET", "POST"])
@login_required
def new():
    """Reaching here via post if rating popup is filled and submitted or search/new.html is requested"""
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # movie_id is hidden in form popup
        movie_id = int(request.form.get("movie_id"))
        # checking if movie is in usermovies already
        rows = db.execute("SELECT * FROM usermovies WHERE user_id = :user_id AND movie_id = :movie_id", user_id = session["user_id"], movie_id = movie_id)
        # needs to be float as input can be 7.9
        user_rating = float(request.form.get("rating"))
        notes = request.form.get("notes")
        # movie was in usermovies already -> notes and rating get updated
        if len(rows) != 1:
            db.execute("INSERT INTO usermovies (user_id,movie_id,user_rating,notes) VALUES(:user_id, :movie_id, :user_rating, :notes)", user_id = session["user_id"], movie_id = movie_id, user_rating = user_rating, notes = notes)
            db.execute("DELETE FROM watchlist WHERE user_id = :user_id AND movie_id = :movie_id", user_id = session["user_id"], movie_id = movie_id)
            # # flash('rated.')
        # movie was not present in usermovies -> is inserted
        else:
            db.execute("UPDATE usermovies SET user_rating = :user_rating, notes = :notes WHERE user_id = :user_id AND movie_id = :movie_id", user_rating = user_rating, notes = notes, user_id = session["user_id"], movie_id = movie_id)
            # # flash('updated.')
        # Redirect user to home page to see user's movies
        return redirect("/index")
    # if reached via get method
    else:
        return render_template("new.html")


@app.route("/stats", methods = ["GET", "POST"])
@login_required
def stats():
    """Getting some basic stats for stars or directors"""
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        directorraw = request.form.get("director")
        starraw = request.form.get("star")
        if starraw:
            # string formatting so input can be used with LIKE in sql query
            star = f"%{starraw}%"
            rows = db.execute("SELECT COUNT(ratings.rating) as count, AVG(ratings.rating) as avg FROM ratings JOIN movies ON ratings.movie_id = movies.id JOIN stars ON movies.id = stars.movie_id JOIN people ON stars.person_id = people.id WHERE name LIKE :name", name = star)
            star = star
            return render_template("stats.html", rows = rows, star = starraw)
        if directorraw:
            # string formatting so input can be used with LIKE in sql query
            director = f"%{directorraw}%"
            rows = db.execute("SELECT COUNT(ratings.rating) as count, AVG(ratings.rating) as avg FROM ratings JOIN movies ON ratings.movie_id = movies.id JOIN directors ON movies.id = directors.movie_id JOIN people ON directors.person_id = people.id WHERE name LIKE :name", name = director)
            director = director
            return render_template("stats.html", rows = rows, director = directorraw)
            
    else:
        rows = 0
        return render_template("stats.html", rows = rows)


@app.route("/randomizer", methods = ["GET", "POST"])
@login_required
def randomizer():
    """Randomized Search for Movies"""
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # getting all input forms
        randomstar = request.form.get("randomstar")
        randomyear = request.form.get("randomyear")
        randomdirector = request.form.get("randomdirector")
        # checking which one was provided
        if randomstar:
            query = randomstar
            # string formatting so input can be used with LIKE in sql query
            randomstar = f"%{randomstar}%"
            random = db.execute("SELECT * FROM movies JOIN ratings ON movies.id = ratings.movie_id JOIN stars ON movies.id = stars.movie_id JOIN people ON stars.person_id = people.id WHERE name LIKE :name ORDER BY RANDOM() LIMIT 1", name = randomstar)
            method = 'star'
        elif randomyear:
            query = randomyear
            try:
                randomyear = int(randomyear)
                if randomyear > 2050 or randomyear < 1970:
                    flash('Year must be between 1970 and 2050.')
                    return redirect('/randomizer')
            except:
                flash('Input must be numeric.')
                return redirect('/randomizer')
            random = db.execute("SELECT * FROM movies JOIN ratings ON movies.id = ratings.movie_id WHERE year = :year ORDER BY RANDOM() LIMIT 1", year = randomyear)
            method = 'year'
            for row in random:
                row["name"] = str(randomyear)
        elif randomdirector:
            query = randomdirector
            randomdirector = f"%{randomdirector}%"
            random = db.execute("SELECT * FROM movies JOIN ratings ON movies.id = ratings.movie_id JOIN directors ON movies.id = directors.movie_id JOIN people ON directors.person_id = people.id WHERE name LIKE :name ORDER BY RANDOM() LIMIT 1", name = randomdirector)
            method = 'director'
        if len(random) == 0:
            random = 0
            flash('Sorry, no movie found for this query.')
            return redirect('/randomizer')
        else:
            return render_template("randomizer.html", random = random, method = method, query = query)
    else:
        # passing random = 0, so randomizer.html is rendered without result for randomized search
        random = 0
        return render_template("randomizer.html", random = random)


@app.route("/shuffle")
@login_required
def shuffle():
    # requesting method stored in button id
    method = request.args.get('method', 0, type=str)
    if method == 'star':
        # requesting query from based on column
        query = request.args.get('query', 0, type=str)
        randomstar = f"%{query}%"
        random = db.execute("SELECT * FROM movies JOIN ratings ON movies.id = ratings.movie_id JOIN stars ON movies.id = stars.movie_id JOIN people ON stars.person_id = people.id WHERE name LIKE :name ORDER BY RANDOM() LIMIT 1", name = randomstar)
    elif method == 'director':
        query = request.args.get('query', 0, type=str)
        randomdirector = f"%{query}%"
        random = db.execute("SELECT * FROM movies JOIN ratings ON movies.id = ratings.movie_id JOIN directors ON movies.id = directors.movie_id JOIN people ON directors.person_id = people.id WHERE name LIKE :name ORDER BY RANDOM() LIMIT 1", name = randomdirector)
    elif method == 'year':
        query = request.args.get('query', 0, type=int)
        randomyear = int(query)
        random = db.execute("SELECT * FROM movies JOIN ratings ON movies.id = ratings.movie_id WHERE year = :year ORDER BY RANDOM() LIMIT 1", year = randomyear)
    # initializing individual variables to pass back to jquery function
    for row in random:
        title = row["title"]
        movie_id = row["movie_id"]
        year = row["year"]
        rating = row["rating"]
        if len(str(movie_id)) == 5:
            link = "https://www.imdb.com/title/tt00"
        elif len(str(movie_id)) == 6:
            link = "https://www.imdb.com/title/tt0"
        elif len(str(movie_id)) == 7 or len(str(movie_id)) == 8:
            link = "https://www.imdb.com/title/tt"
        try:
            # row name only present, if randomized by star or director
            name = row["name"]
            return jsonify(method = method, name = name, query = query, year = year, rating = rating, movie_id = movie_id, title = title, link = link)
        except:
            # otherwise pass w/o name
            return jsonify(method = method, query = query, year = year, rating = rating, movie_id = movie_id, title = title, link = link)


@app.route("/recommendations", methods = ["GET", "POST"])
@login_required
def recommendations():
    """Generate Recommendations based on Top rated Movies and their respective directors and stars"""
    # route if user wants to change number of entries per table
    if request.method == "POST":
        # checking to see how many entries user wants to see
        number = int(request.form.get("number"))
    else:
        # 3 entries by default
        number = 3
    # you might also like based on directors (super long because movie should not be in wl or in movies and need to JOIN multiple tables):
    random = db.execute("SELECT * FROM movies JOIN directors ON movies.id = directors.movie_id JOIN people ON directors.person_id = people.id JOIN ratings ON movies.id = ratings.movie_id WHERE name IN (SELECT name FROM people JOIN directors ON people.id = directors.person_id JOIN movies ON directors.movie_id = movies.id WHERE movies.id IN (SELECT usermovies.movie_id FROM usermovies JOIN movies ON usermovies.movie_id = movies.id JOIN ratings ON movies.id = ratings.movie_id  WHERE user_id = :user_id ORDER BY user_rating DESC LIMIT :number) ORDER BY RANDOM() LIMIT :number) AND movies.id NOT IN (SELECT movie_id FROM usermovies WHERE usermovies.user_id = :user_id) AND movies.id NOT IN (SELECT movie_id FROM watchlist WHERE watchlist.user_id = :user_id) ORDER BY RANDOM() LIMIT :number", user_id = session["user_id"], number = number)
    # you might also like based on stars:
    random2 = db.execute("SELECT * FROM movies JOIN stars ON movies.id = stars.movie_id JOIN people ON stars.person_id = people.id JOIN ratings ON movies.id = ratings.movie_id WHERE name IN (SELECT name FROM people JOIN stars ON people.id = stars.person_id JOIN movies ON stars.movie_id = movies.id WHERE movies.id IN (SELECT usermovies.movie_id FROM usermovies JOIN movies ON usermovies.movie_id = movies.id JOIN ratings ON movies.id = ratings.movie_id  WHERE user_id = :user_id ORDER BY user_rating DESC LIMIT :number) ORDER BY RANDOM() LIMIT :number) AND movies.id NOT IN (SELECT movie_id FROM usermovies WHERE usermovies.user_id = :user_id) AND movies.id NOT IN (SELECT movie_id FROM watchlist WHERE watchlist.user_id = :user_id) ORDER BY RANDOM() LIMIT :number", user_id = session["user_id"], number = number)
    # passing back our random top :number back to jquery
    return render_template("recommendations.html", number = number, random = random, random2 = random2)
    
    
@app.route("/favourites", methods = ["GET", "POST"])
@login_required
def favourites():
    """User's Favourites"""
    # route if user wants to change number of entries per table
    if request.method == "POST":
        # checking to see how many entries user wants to see
        number = int(request.form.get("number"))
    else:
        # 5 entries by default
        number = 5
    # query for the requested number of entries
    movies = db.execute("SELECT * FROM usermovies JOIN movies ON usermovies.movie_id = movies.id JOIN ratings ON movies.id = ratings.movie_id  WHERE user_id = :user_id ORDER BY user_rating DESC LIMIT :number", number = number, user_id = session["user_id"])
    for movie in movies:
        # making additional querie for each movie to get directors names in additional column
        name = db.execute("SELECT name FROM people JOIN directors ON people.id = directors.person_id JOIN movies ON directors.movie_id = movies.id WHERE movies.id = :movie_id", movie_id = movie["id"])
        movie["name"] = name[0]["name"]
    # for html to access for header  "here, your x results:"
    number = len(movies)
    # passing movietable and number back to favourites.html
    return render_template("favourites.html", movies = movies, number = number)
    

@app.route("/watchlist", methods = ["GET", "POST"])
@login_required
def watchlist():
    """Shows all movies on user's watchlist"""
    if request.method == "GET":
        # getting all entries from watchlist for the user
        rows = db.execute("SELECT * FROM watchlist JOIN directors ON watchlist.movie_id = directors.movie_id JOIN movies ON watchlist.movie_id = movies.id JOIN ratings ON movies.id = ratings.movie_id JOIN people ON directors.person_id = people.id WHERE user_id = :user_id", user_id = session["user_id"])
        return render_template("watchlist.html", rows = rows)


@app.route('/add_watchlist')
@login_required
def add_watchlist():
    """Getting here from jQuery to add a movie to the watchlist"""
    movie_id = request.args.get('a', 0, type=int)
    rows = db.execute("SELECT movie_id FROM watchlist WHERE user_id = :user_id AND movie_id = :movie_id", user_id = session["user_id"], movie_id = movie_id)
    if len(rows) == 0:
        db.execute("INSERT INTO watchlist (user_id,movie_id) VALUES(:user_id, :movie_id)", user_id = session["user_id"], movie_id = movie_id)
    else:
        flash('Movie already in watchlist.')
    return jsonify(calculate='Added', movie_id = movie_id)


@app.route('/add_rate')
@login_required
def add_rate():
    """Testing jQuery"""
    # getting here when rate button is clicked -> getting input arguments from input form and hidden h4 in "form"
    movie_id = request.args.get('a', 0, type=int)
    user_rating = request.args.get('b', 0, type=float)
    notes = request.args.get('c', 0, type=str)
    # getting old entry, if one is already there for the movie
    rows = db.execute("SELECT * FROM usermovies WHERE user_id = :user_id AND movie_id = :movie_id", user_id = session["user_id"], movie_id = movie_id)
    for row in rows:
        # making a variable with the old notes, so that the respective id (id is the old notes) of the notes html element can be accessed
        oldnotes = row["notes"]
    try:
        print(oldnotes)
    except:
        # in the case of no entry (needed for html to check)
        oldnotes = 0
        
    print(oldnotes)
    if len(rows) != 1:
        # movie was not in usermovies yet -> delete from watchlist and insert into usermovies
        db.execute("INSERT INTO usermovies (user_id,movie_id,user_rating,notes) VALUES(:user_id, :movie_id, :user_rating, :notes)", user_id = session["user_id"], movie_id = movie_id, user_rating = user_rating, notes = notes)
        db.execute("DELETE FROM watchlist WHERE user_id = :user_id AND movie_id = :movie_id", user_id = session["user_id"], movie_id = movie_id)
    else:
        # movie was in usermovies already -> update of old entry
        db.execute("UPDATE usermovies SET user_rating = :user_rating, notes = :notes WHERE user_id = :user_id AND movie_id = :movie_id", user_rating = user_rating, notes = notes, user_id = session["user_id"], movie_id = movie_id)
    user_rating = str(user_rating)
    return jsonify(calculate=' Rated', movie_id = movie_id, notes = notes, oldnotes = oldnotes, user_rating = user_rating)
    

@app.route("/clear", methods = ["GET", "POST"])
@login_required
def clear():
    """Clear either Watchlist or Movies in User's Database"""
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # name of button is either "allmv/allwl" or "{{id}}mw/{{id}}wl" -> this name is transferred (via jquery fct) into value of "amount" input fields of the popup for confirming the clearing
        # checking if one or all movies shall be cleared
        if "all" in request.form["amount"]:
            # checking if clearing should be done for watchlist or movies
            if "wl" in request.form["amount"]:
                db.execute("DELETE FROM watchlist WHERE user_id = :user_id", user_id = session["user_id"])
                flash('Watchlist cleared.')
                return render_template('watchlist.html')
            elif "mv" in request.form["amount"]:
                db.execute("DELETE FROM usermovies WHERE user_id = :user_id", user_id = session["user_id"])
                flash('Movies cleared.')
                return render_template('index.html')
        else:
            # only one specific movie shall be cleared
            movie_id = request.form["amount"]
            if "wl" in movie_id:
                movie_id = int(movie_id.replace('wl', ''))
                db.execute("DELETE FROM watchlist WHERE user_id = :user_id AND movie_id = :movie_id", user_id = session["user_id"], movie_id = movie_id)
                flash('Cleared.')
                return redirect('/watchlist')
            elif "mv" in movie_id:
                movie_id = int(movie_id.replace('mv', ''))
                db.execute("DELETE FROM usermovies WHERE user_id = :user_id AND movie_id = :movie_id", user_id = session["user_id"], movie_id = movie_id)
                flash('Cleared.')
                return redirect('/index')


@app.route("/login", methods = ["GET", "POST"])
def login():
    """Log user in"""
    # Forget any user_id
    session.clear()
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        username = request.form.get("username")
        # Ensure username was submitted
        if not username:
            flash('Must provide username.')
            return render_template("login.html")
        # Ensure password was submitted
        elif not request.form.get("password"):
            flash('Must provide password.')
            return render_template("login.html")
            # return apology("must provide password", 403)
        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username = username)
        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            flash('Invalid username and/or password.')
            return render_template("login.html")
            # return apology("invalid username and/or password", 403)
        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]
        # Redirect user to home page
        flash(f'Hello {username}.')
        return redirect("/index")
    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""
    # Forget any user_id
    session.clear()
    # Redirect user to login form
    return redirect("/index")


@app.route("/pw", methods = ["GET", "POST"])
@login_required
def pw():
    """Change password."""
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # getting passwords from form
        oldpassword = request.form.get("oldpassword")
        newpassword = request.form.get("newpassword")
        confirmation = request.form.get("confirmation")
        # if new password and confirmation don't match:
        if newpassword != confirmation:
            flash('Passwords do not match.')
            return redirect('/pw')
            # return apology("passwords do not match", 403)
        # if new pw is equal to old -> no need to continue
        if oldpassword == newpassword:
            flash('Old and new passwords are the same.')
            return redirect('/pw')
            # return apology("passwords are the same", 403)
        # Query database for pw hash from user
        rows = db.execute("SELECT hash FROM users WHERE id = :id", id = session["user_id"])
        # if check_password_hash function reveals that pws don't match -> apology
        if not check_password_hash(rows[0]["hash"], oldpassword):
            flash('Old password is not correct.')
            return redirect('/pw')
            # return apology("old password is not correct", 403)
        # otherwise set the new password and update database
        db.execute("UPDATE users SET hash = :hash WHERE id = :id", hash = generate_password_hash(newpassword), id = session["user_id"])
        # Redirect user to home (and show message maybe?)
        flash('Password changed.')
        return redirect("/index")
    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("pw.html")


@app.route("/register", methods = ["GET", "POST"])
def register():
    """Register user"""
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            flash('Must provide username.')
            return redirect('/register')
            # return apology("must provide username", 403)
        # Ensure password was submitted
        elif not request.form.get("password"):
            flash('Must provide password.')
            return redirect('/register')
            # return apology("must provide password", 403)
        # Ensure that password and confirmation password match
        elif request.form.get("password") != request.form.get("confirmation"):
            flash('Provided passwords do not match.')
            return redirect('/register')
            # return apology("passwords provided do not match", 403)
        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username", username = request.form.get("username"))
        # Ensure username doesn't already exists
        if len(rows) == 1:
            flash('Username already exists.')
            return redirect('/register')
            # return apology("username already exists", 403)
        else:
            username = request.form.get("username")
            hash = generate_password_hash(request.form.get("password"))
            # insert new user into our database but best not to do with string concatenation because of potentia SQL injection attacks
            db.execute("INSERT INTO users (username, hash) VALUES (:username, :hash)", username = username, hash = hash)
            # Logging in user as there is no need to make user log in after registering
            rows = db.execute("SELECT * FROM users WHERE username = :username", username = request.form.get("username"))
            # Remember which user has logged in
            session["user_id"] = rows[0]["id"]
            # Redirect user to home (and show message maybe?)
            flash(f'Welcome to MyMDb, {username}.')
            return redirect("/index")
    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)

# these lines are needed in order to run the web app outside cs50ide in a local environment
if __name__ == "__main__":
    from waitress import serve
    serve(app, host="0.0.0.0", port=8080)