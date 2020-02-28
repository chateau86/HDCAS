#!/usr/bin/env python3

print("Server code goes here")

import flask

app = flask.Flask(__name__)
app.config["DEBUG"] = True


@app.route('/', methods=['GET'])
def home():
    return "<h1>It's alive!!!</h1>"
