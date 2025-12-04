from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session, jsonify
from flask_session import Session
import os
from dotenv import load_dotenv, find_dotenv
dotenv_path = find_dotenv()
load_dotenv(dotenv_path)
database_url = os.getenv("database")
db = SQL(database_url)

app = Flask(__name__)

@app.route("/")
def index():

    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)