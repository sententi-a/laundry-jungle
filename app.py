from flask import render_template, Flask, jsonify
from pymongo import MongoClient

app = Flask(__name__)

@app.route('/')
def login():
    pass

