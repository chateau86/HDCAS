#!/usr/bin/env python3

# run `flask run --host=0.0.0.0`

import os
from datetime import datetime

import flask
from flask import request
from flask_sqlalchemy import SQLAlchemy

import simplejson

app = flask.Flask(__name__)
app.config["DEBUG"] = True,
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DB_URL']

db = SQLAlchemy(app)

# Will not overwrite existing table per
# https://docs.sqlalchemy.org/en/13/core/metadata.html#sqlalchemy.schema.MetaData.create_all

print("Server init ok")
print("DB URL: "+os.environ['DB_URL'])


class test_message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    msg = db.Column(db.String())
    timestamp = db.Column(db.DateTime(timezone=False), default=datetime.utcnow)

    def __repr__(self):
        return self.id + " " + self.timestamp + ": " + self.msg


@app.route('/', methods=['GET'])
def home():
    return "<h1>It's alive!!!</h1>"


@app.route('/msg', methods=['GET'])
def read_msg():
    messages = db.session \
        .query(test_message) \
        .order_by(test_message.timestamp) \
        .all()
    print(messages)
    return simplejson.dumps(messages)


@app.route('/send', methods=['POST'])
def put_test_msg():
    msg = request.form["msg"]
    print("Got msg: " + msg)
    db.session.add(test_message(msg=msg))
    db.session.commit()
    return "<h1>Msg recieved</h1>"


db.create_all()
