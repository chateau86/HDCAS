#!/usr/bin/env python3

# run `flask run --host=0.0.0.0`

import os

import flask
from flask_sqlalchemy import SQLAlchemy

app = flask.Flask(__name__)
app.config["DEBUG"] = True,
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DB_URL']

print("Server init ok")
print("DB URL: "+os.environ['DB_URL'])

@app.route('/', methods=['GET'])
def home():
    return "<h1>It's alive!!!</h1>"
