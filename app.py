from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session, jsonify
from flask_session import Session
import os
from dotenv import load_dotenv, find_dotenv
from flask_bcrypt import Bcrypt
from functools import wraps
from urllib.parse import urlparse
import re
dotenv_path = find_dotenv()
load_dotenv(dotenv_path)
database_url = os.getenv("database")
db = SQL(database_url)

app = Flask(__name__)
Bcrypt = Bcrypt(app)
# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

def is_valid_name(name):
    pattern = r"[A-Za-z0-9][A-Za-z0-9 ]*"
    return re.fullmatch(pattern, name) is not None
def generate_password_hash(password):
    return Bcrypt.generate_password_hash(password).decode('utf-8')
def check_password_hash(pw_hash, password):
    return Bcrypt.check_password_hash(pw_hash, password)

def delete_folder_and_contents(folder_id, user_id):
    # Delete all links in the folder
    db.execute("DELETE FROM links WHERE folder_id = ? AND user_id = ?", folder_id, user_id)

    # Find all subfolders
    subfolders = db.execute("SELECT id FROM folders WHERE parent_id = ? AND user_id = ?", folder_id, user_id)

    # Recursively delete subfolders and their contents
    for subfolder in subfolders:
        delete_folder_and_contents(subfolder["id"], user_id)

    # Finally, delete the folder itself
    db.execute("DELETE FROM folders WHERE id = ? AND user_id = ?", folder_id, user_id)
def apology(message, code=400):
    """Render message as an apology to user."""

    def escape(s):
        """
        Escape special characters.

        https://github.com/jacebrowning/memegen#special-characters
        """
        for old, new in [
            ("-", "--"),
            (" ", "-"),
            ("_", "__"),
            ("?", "~q"),
            ("%", "~p"),
            ("#", "~h"),
            ("/", "~s"),
            ('"', "''"),
        ]:
            s = s.replace(old, new)
        return s
    if session.get("user_id") is None:
        return render_template("apology.html", top=code, message=message, bodyclass="small-body", noLogout=True), code
    return render_template("apology.html", top=code, message=message, bodyclass="small-body"), code

@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

def login_required(f):
    """
    Decorate routes to require login.

    https://flask.palletsprojects.com/en/latest/patterns/viewdecorators/
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)

    return decorated_function


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        if not request.form.get("username"):
            return apology("Please enter a valid username")
        if not request.form.get("password"):
            return apology("Please enter a valid password")
        if request.form.get("password") != request.form.get("confirmation"):
            return apology("Password confirmation must match the password")
        try:
            db.execute("INSERT INTO users (username, password_hash) VALUES(?, ?)", request.form.get(
                "username"), generate_password_hash(request.form.get("password")))
        except ValueError:
            return apology("User already exists")
        else:
            db.execute("INSERT INTO folders (user_id, name, parent_id) VALUES(?, ?, ?)",
                       db.execute("SELECT id FROM users WHERE username = ?", request.form.get("username"))[0]["id"], "root", None)
            return redirect("/")

    return render_template("register.html", bodyclass="small-body", noLogout=True)
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
        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get("username")
        )

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(
            rows[0]["password_hash"], request.form.get("password")
        ):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]
        # Remember user root folder.
        session["root_folder_id"] = db.execute(
            "SELECT id FROM folders WHERE user_id = ? AND parent_id IS NULL", session["user_id"]
        )[0]["id"]
        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html", bodyclass="small-body", noLogout=True)
    

@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/login")


#load user's folders helpers:
def get_folder_rows(user_id,):
    rows = db.execute(
        "SELECT id, name, parent_id FROM folders WHERE user_id = ?",
        user_id,
    )
    return rows

def get_links_rows(user_id):
    rows = db.execute(
        "SELECT id, name, folder_id, url, description FROM links WHERE user_id = ?",
        user_id,
    )
    return rows

def build_folder_tree_with_links(folder_rows, link_rows, root_id=None):
    # base folder nodes
    by_id = {
        row["id"]: {
            "id": row["id"],
            "name": row["name"],
            "children": [],
            "links": [],          # <- will fill this
        }
        for row in folder_rows
    }

    # attach children folders
    roots = []
    for row in folder_rows:
        fid = row["id"]
        pid = row["parent_id"]
        node = by_id[fid]

        if pid is None:
            roots.append(node)
        else:
            parent = by_id.get(pid)
            if parent:
                parent["children"].append(node)

    # attach links to their folders
    for l in link_rows:
        folder_id = l["folder_id"]
        if folder_id in by_id:
            by_id[folder_id]["links"].append(
                {
                    "id": l["id"],
                    "name": l["name"],
                    "url": l["url"],
                    "description": l["description"],
                }
            )

    if root_id is None:
        return roots
    return [by_id[root_id]] if root_id in by_id else []


@app.route("/create-link", methods=["POST", "GET"])
@login_required
def create_link():
    root_folder_id = session["root_folder_id"]
    rq = request.get_json()
    name = rq["name"]
    url = rq["url"]
    description = rq["description"]
    folder_id = rq["current_folder"]
    user_id = session["user_id"]
    if not name or not url or not folder_id:
        return jsonify({"error": "Missing required fields"}), 400
    if is_valid_name(name) == False:
        return jsonify({"error": "Name must be alphanumeric"}), 400
    if len(name) > 100:
        return jsonify({"error": "Name too long"}), 400
    folder_id = db.execute("SELECT id FROM folders WHERE id = ? AND user_id = ?", folder_id, user_id)[0]["id"]
    if not folder_id:
        return jsonify({"error": "Invalid folder"}), 400
    try:
        parsed_url = urlparse(url)
        if not all([parsed_url.scheme, parsed_url.netloc]):
            return jsonify({"error": "Invalid URL"}), 400
        db.execute("INSERT INTO links (user_id, name, folder_id, url, description) VALUES(?, ?, ?, ?, ?)",
                   user_id, name, folder_id, url, description)
        folder_rows = get_folder_rows(user_id)
        link_rows = get_links_rows(user_id)
        folders_tree_with_links = build_folder_tree_with_links(folder_rows, link_rows, root_folder_id)
        return jsonify(folders_tree_with_links), 200
    except ValueError:
        return jsonify({"error": "Invalid URL"}), 400
@app.route("/delete-link", methods=["POST"])
@login_required
def delete_link():
    rq = request.get_json()
    link_id = rq["link_id"]
    user_id = session["user_id"]
    try:
        db.execute("DELETE FROM links WHERE id = ? AND user_id = ?", link_id, user_id)
    except ValueError:
        return jsonify({"error": "Could not delete link"}), 400
    root_folder_id = session["root_folder_id"] 
    folder_rows = get_folder_rows(user_id)
    link_rows = get_links_rows(user_id)
    folders_tree_with_links = build_folder_tree_with_links(folder_rows, link_rows, root_folder_id)
    return jsonify(folders_tree_with_links), 200
@app.route("/create-folder", methods=["POST"])
@login_required
def create_folder():
    rq = request.get_json()
    name = rq["name"]
    current_folder = rq["current_folder"]
    if not name or not current_folder:
        return jsonify({"error": "Missing required fields"}), 400
    if is_valid_name(name) == False:
        return jsonify({"error": "Name must be alphanumeric"}), 400
    if len(name) > 100:
        return jsonify({"error": "Name too long"}), 400
    user_id = session["user_id"]
    parent_folder = db.execute("SELECT id FROM folders WHERE id = ? AND user_id = ?", current_folder, user_id)
    if not parent_folder:
        return jsonify({"error": "Invalid parent folder"}), 400
    try:
        db.execute("INSERT INTO folders (user_id, name, parent_id) VALUES(?, ?, ?)",
                   user_id, name, current_folder)
        root_folder_id = session["root_folder_id"]
        folder_rows = get_folder_rows(user_id)
        link_rows = get_links_rows(user_id)
        folders_tree_with_links = build_folder_tree_with_links(folder_rows, link_rows, root_folder_id)
        return jsonify(folders_tree_with_links), 200
    except ValueError:
        return jsonify({"error": "Could not create folder"}), 400
    
@app.route("/delete-folder", methods=["POST"])
@login_required
def delete_folder():
    rq = request.get_json()
    folder_id = rq["folder_id"]
    user_id = session["user_id"]
    if not folder_id:
        return jsonify({"error": "Missing folder ID"}), 400
    folder = db.execute("SELECT id FROM folders WHERE id = ? AND user_id = ?", folder_id, user_id)
    if not folder:
        return jsonify({"error": "Invalid folder"}), 400
    try:
        delete_folder_and_contents(folder_id, user_id)
        root_folder_id = session["root_folder_id"]
        folder_rows = get_folder_rows(user_id)
        link_rows = get_links_rows(user_id)
        folders_tree_with_links = build_folder_tree_with_links(folder_rows, link_rows, root_folder_id)
        return jsonify(folders_tree_with_links), 200
    except ValueError:
        return jsonify({"error": "Could not delete folder"}), 400
    
@app.route("/rename-folder", methods=["POST"])
@login_required
def rename_folder():
    rq = request.get_json()
    folder_id = rq["folder_id"]
    new_name = rq["new_name"]
    user_id = session["user_id"]
    if not folder_id or not new_name:
        return jsonify({"error": "Missing required fields"}), 400
    if is_valid_name(new_name) == False:
        return jsonify({"error": "Name must be alphanumeric"}), 400
    if len(new_name) > 100:
        return jsonify({"error": "Name too long"}), 400
    folder = db.execute("SELECT id FROM folders WHERE id = ? AND user_id = ?", folder_id, user_id)
    if not folder:
        return jsonify({"error": "Invalid folder"}), 400
    try:
        db.execute("UPDATE folders SET name = ? WHERE id = ? AND user_id = ?", new_name, folder_id, user_id)
        root_folder_id = session["root_folder_id"]
        folder_rows = get_folder_rows(user_id)
        link_rows = get_links_rows(user_id)
        folders_tree_with_links = build_folder_tree_with_links(folder_rows, link_rows, root_folder_id)
        return jsonify(folders_tree_with_links), 200
    except ValueError:
        return jsonify({"error": "Could not rename folder"}), 400
@app.route("/")
@login_required
def index():
    user_id = session["user_id"]
    root_folder_id = session["root_folder_id"]
    folder_rows = get_folder_rows(user_id)
    link_rows = get_links_rows(user_id)

    folders_tree_with_links = build_folder_tree_with_links(folder_rows, link_rows, root_folder_id)
    return render_template("index.html", folders=folders_tree_with_links, bodyclass="index-body", username=db.execute("SELECT username FROM users WHERE id = ?", user_id)[0]["username"])
@app.route("/rename-link", methods=["POST"])
@login_required
def rename_link():
    rq = request.get_json()
    link_id = rq["link_id"]
    new_name = rq["new_name"]
    user_id = session["user_id"]
    if not link_id or not new_name:
        return jsonify({"error": "Missing required fields"}), 400
    if is_valid_name(new_name) == False:
        return jsonify({"error": "Name must be alphanumeric"}), 400
    if len(new_name) > 100:
        return jsonify({"error": "Name too long"}), 400
    link = db.execute("SELECT id FROM links WHERE id = ? AND user_id = ?", link_id, user_id)
    if not link:
        return jsonify({"error": "Invalid link"}), 400
    try:
        db.execute("UPDATE links SET name = ? WHERE id = ? AND user_id = ?", new_name, link_id, user_id)
        root_folder_id = session["root_folder_id"]
        folder_rows = get_folder_rows(user_id)
        link_rows = get_links_rows(user_id)
        folders_tree_with_links = build_folder_tree_with_links(folder_rows, link_rows, root_folder_id)
        return jsonify(folders_tree_with_links), 200
    except ValueError:
        return jsonify({"error": "Could not rename link"}), 400

if __name__ == "__main__":
    app.run(debug=True)


